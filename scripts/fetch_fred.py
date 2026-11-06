#!/usr/bin/env python3
"""Fetch every FRED series listed in catalog.json into data/<ID>.csv and write
data/manifest.json. Standard library only, so it runs anywhere (GitHub Actions,
a laptop, a cron job) with no installs.

Usage: python3 scripts/fetch_fred.py [--catalog catalog.json] [--out data] [--workers 6]
"""
import argparse, csv, io, json, os, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={id}"
UA = "econ-dashboards fetcher (github pages site; stdlib urllib)"


def fetch_one(sid, retries=3):
    url = FRED_CSV.format(id=sid)
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                text = r.read().decode("utf-8-sig")
            rows = list(csv.reader(io.StringIO(text)))
            if not rows or len(rows[0]) < 2 or rows[0][0] != "observation_date":
                raise ValueError(f"unexpected response header: {rows[:1]}")
            out = []
            for d, v in (r[:2] for r in rows[1:] if len(r) >= 2):
                if v in ("", ".", "NA"):
                    continue
                out.append((d, v))
            if not out:
                raise ValueError("no observations")
            return sid, out, None
        except (urllib.error.HTTPError, urllib.error.URLError, ValueError, OSError) as e:
            last_err = e
            if isinstance(e, urllib.error.HTTPError) and e.code in (400, 404):
                break  # unknown series id, do not retry
            time.sleep(2 * (attempt + 1))
    return sid, None, str(last_err)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", default="catalog.json")
    ap.add_argument("--out", default="data")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()

    with open(args.catalog) as f:
        catalog = json.load(f)
    ids = sorted({s["id"] for d in catalog["dashboards"] for p in d["panels"] for s in p["series"]})
    os.makedirs(args.out, exist_ok=True)

    manifest_path = os.path.join(args.out, "manifest.json")
    old = {}
    if os.path.exists(manifest_path):
        try:
            old = json.load(open(manifest_path)).get("series", {})
        except Exception:
            old = {}

    results, failures = {}, {}
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(fetch_one, sid) for sid in ids]
        for fut in as_completed(futs):
            sid, obs, err = fut.result()
            if obs is None:
                failures[sid] = err
                continue
            path = os.path.join(args.out, f"{sid}.csv")
            with open(path, "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["date", "value"])
                w.writerows(obs)
            results[sid] = {
                "first": obs[0][0], "last": obs[-1][0],
                "last_value": float(obs[-1][1]), "count": len(obs),
                "prev_value": float(obs[-2][1]) if len(obs) > 1 else None,
                "source": f"https://fred.stlouisfed.org/series/{sid}",
            }
            print(f"ok   {sid:<18} {obs[0][0]} .. {obs[-1][0]}  ({len(obs)} obs)")

    for sid, err in sorted(failures.items()):
        print(f"FAIL {sid:<18} {err}", file=sys.stderr)
        if sid in old:  # keep the previous good copy and its metadata
            results[sid] = dict(old[sid], stale=True)

    manifest = {
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "series_count": len(results), "failed": sorted(failures),
        "series": dict(sorted(results.items())),
    }
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=1)
    print(f"\n{len(results)} series written, {len(failures)} failed -> {manifest_path}")
    # Exit non-zero only if nothing could be fetched at all (network down).
    sys.exit(1 if results == {} else 0)


if __name__ == "__main__":
    main()
