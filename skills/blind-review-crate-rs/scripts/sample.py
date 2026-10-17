#!/usr/bin/env python3
"""Pick N reviewable .rs files from a crate for blind review.

usage: sample.py CRATE [--count 5] [--seed N] [--weight random|churn|size] [--no-history]
       sample.py CRATE --record FILE...      # append reviewed files to the history

Prints one path per line, relative to CRATE.
"""
import argparse
import random
import subprocess
import sys
from pathlib import Path

SKIP_DIRS = {"__basic__", "tests", "benches", "examples", "target", "generated"}
SKIP_FILES = {"mod.rs", "lib.rs", "main.rs", "build.rs", "constants.rs"}
HISTORY = ".review-history"
GENERATED_MARKERS = ("@generated", "DO NOT EDIT")


def pool(crate: Path) -> list[Path]:
    files = []
    for root in ("src", "methods"):
        base = crate / root
        if not base.is_dir():
            continue
        for path in base.rglob("*.rs"):
            rel = path.relative_to(crate)
            if path.name in SKIP_FILES or SKIP_DIRS & set(rel.parts[:-1]):
                continue
            head = path.read_text(errors="replace")[:500]
            if any(marker in head for marker in GENERATED_MARKERS):
                continue
            files.append(rel)
    return sorted(files)


def churn(crate: Path) -> dict[str, int]:
    try:
        out = subprocess.run(
            ["git", "log", "--name-only", "--pretty=format:", "--relative", "--", "."],
            cwd=crate, capture_output=True, text=True, check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {}
    counts: dict[str, int] = {}
    for line in filter(None, out.splitlines()):
        counts[line] = counts.get(line, 0) + 1
    return counts


def weighted_sample(items, weights, k, rng):
    items, weights, picked = list(items), list(weights), []
    while items and len(picked) < k:
        i = rng.choices(range(len(items)), weights=weights)[0]
        picked.append(items.pop(i))
        weights.pop(i)
    return picked


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("crate", type=Path)
    ap.add_argument("--count", type=int, default=5)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--weight", choices=["random", "churn", "size"], default="random")
    ap.add_argument("--no-history", action="store_true")
    ap.add_argument("--record", nargs="+", metavar="FILE")
    args = ap.parse_args()
    crate = args.crate.resolve()
    history = crate / HISTORY

    if args.record:
        with history.open("a") as fh:
            fh.writelines(f"{f}\n" for f in args.record)
        return 0

    candidates = pool(crate)
    if not args.no_history and history.exists():
        seen = set(history.read_text().split())
        fresh = [f for f in candidates if str(f) not in seen]
        if not fresh:
            print(f"# history exhausted; delete {history} to start over", file=sys.stderr)
        candidates = fresh

    if args.weight == "churn":
        counts = churn(crate)
        weights = [counts.get(str(f), 0) + 1 for f in candidates]
    elif args.weight == "size":
        weights = [(crate / f).stat().st_size + 1 for f in candidates]
    else:
        weights = [1] * len(candidates)

    seed = args.seed if args.seed is not None else random.randrange(10**6)
    print(f"# seed={seed} pool={len(candidates)}", file=sys.stderr)
    for f in weighted_sample(candidates, weights, args.count, random.Random(seed)):
        print(f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
