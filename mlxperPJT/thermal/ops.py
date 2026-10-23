"""Read-only, bounded context for eMach. Standard library only; no solver imports.

python -B -X utf8 mlxperPJT/thermal/ops.py snapshot [--live]
python -B -X utf8 mlxperPJT/thermal/ops.py stages --chain e10 --query mapdl
python -B -X utf8 mlxperPJT/thermal/ops.py artifacts
python -B -X utf8 mlxperPJT/thermal/ops.py evidence path/to/result.json --pointer /metrics
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
DEFAULT_REPO = Path(__file__).resolve().parents[2]
THERMAL_REL = Path("mlxperPJT/thermal")


def git(repo, *args, optional=False):
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0")
    result = subprocess.run(
        ["git", "-c", "credential.interactive=false", "-C", str(repo), *args],
        capture_output=True, encoding="utf-8", errors="replace", env=env, timeout=20,
    )
    if result.returncode:
        if optional:
            return None
        raise ValueError("git " + args[0] + " failed: " + result.stderr.strip()[:300])
    return result.stdout


def changes(raw, limit):
    records = iter(raw.split("\0"))
    counts, paths = Counter(), []
    for record in records:
        if not record:
            continue
        code, path = record[:2], record[3:]
        if "R" in code or "C" in code:
            next(records, None)  # -z gives destination first, then original path.
        counts["files"] += 1
        if code == "??":
            counts["untracked"] += 1
        else:
            counts["tracked"] += 1
            counts["staged"] += code[0] != " "
            counts["unstaged"] += code[1] != " "
            counts["conflicts"] += "U" in code or code in ("AA", "DD")
        if len(paths) < limit:
            paths.append({"status": code, "path": path})
    return {"counts": dict(counts), "paths": paths,
            "omitted_paths": counts["files"] - len(paths), "ignored_files_included": False}


def relation(repo, local, remote):
    if local == remote:
        return {"relation": "identical", "local_only": 0, "remote_only": 0}
    if git(repo, "cat-file", "-e", remote + "^{commit}", optional=True) is None:
        return {"relation": "unknown", "reason": "remote commit unavailable locally; no fetch performed"}
    if git(repo, "rev-parse", "--is-shallow-repository").strip() == "true":
        return {"relation": "unknown", "reason": "shallow history; unequal tips cannot prove ancestry"}
    left, right = map(int, git(repo, "rev-list", "--left-right", "--count", local + "..." + remote).split())
    state = "diverged" if left and right else "local_ahead" if left else "local_behind"
    return {"relation": state, "local_only": left, "remote_only": right}


def snapshot(repo, live, limit):
    head = git(repo, "rev-parse", "HEAD").strip()
    branch = (git(repo, "symbolic-ref", "--short", "-q", "HEAD", optional=True) or "").strip()
    upstream = git(repo, "rev-parse", "--symbolic-full-name", "@{upstream}", optional=True)
    result = {"repo": str(repo), "head": head, "branch": branch or "detached",
              "changes": changes(git(repo, "status", "--porcelain=v1", "-z", "--untracked-files=all"), limit),
              "author": {key: (git(repo, "config", "--get", "user." + key, optional=True) or "").strip()
                         for key in ("name", "email")},
              "remote": {"checked_live": False}}
    if upstream:
        sha = git(repo, "rev-parse", "@{upstream}").strip()
        result["cached_upstream"] = {"ref": upstream.strip(), "head": sha,
                                     "freshness": "cached_not_live", **relation(repo, head, sha)}
    agents = repo / "AGENTS.md"
    result["agents_sha256"] = hashlib.sha256(agents.read_bytes()).hexdigest() if agents.is_file() else None
    handoffs = sorted((repo / THERMAL_REL).glob("HANDOFF_????????.md"))
    result["read_next"] = [str(p.relative_to(repo)).replace("\\", "/") for p in
                           ([handoffs[-1]] if handoffs else [])]
    result["read_next"] += ["mlxperPJT/thermal/README.md"]
    if live:
        remote = (git(repo, "config", "--get", "branch." + branch + ".remote", optional=True) or "").strip()
        ref = (git(repo, "config", "--get", "branch." + branch + ".merge", optional=True) or "").strip()
        if not remote or remote == "." or not ref:
            result["remote"] = {"checked_live": False, "reason": "no external upstream configured"}
        else:
            try:
                raw = git(repo, "ls-remote", "--exit-code", remote, ref)
                sha = next(line.split()[0] for line in raw.splitlines() if line.split()[1] == ref)
                result["remote"] = {"checked_live": True, "remote": remote, "ref": ref,
                                    "head": sha, **relation(repo, head, sha)}
            except (ValueError, subprocess.TimeoutExpired, StopIteration) as exc:
                result["remote"] = {"checked_live": False, "reason": str(exc)[:300]}
    return result


def registry(repo):
    # Reuse the existing registry, never invoke its init/check/run entrypoints.
    spec = importlib.util.spec_from_file_location("_emach_pipeline", repo / THERMAL_REL / "pipeline.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def stages(repo, chain, query, limit):
    module = registry(repo)
    if chain and chain not in module.CHAINS:
        raise ValueError("unknown chain; choose " + ", ".join(module.CHAINS))
    matches = [s for s in module.STAGES if (not chain or s.chain == chain) and
               query.casefold() in " ".join((s.id, s.tool, s.desc, s.script)).casefold()]
    return {"source": "mlxperPJT/thermal/pipeline.py", "total": len(matches),
            "items": [{"id": s.id, "tool": s.tool, "mode": s.mode,
                       "script": str(s.path.relative_to(repo)).replace("\\", "/"), "description": s.desc}
                      for s in matches[:limit]], "omitted": max(0, len(matches) - limit),
            "detail_command": "python -B -X utf8 mlxperPJT/thermal/pipeline.py show <stage-id>"}


def stamp(path):
    info = path.stat()
    return {"path": str(path), "bytes": info.st_size,
            "mtime_utc": datetime.fromtimestamp(info.st_mtime, timezone.utc).isoformat()}


def artifacts(repo, limit):
    folders = ["freeflow/data", "prius/data", "thesis_out"]
    rows, errors = [], []
    for folder in folders:
        root = repo / THERMAL_REL / folder
        try:
            if not root.is_dir():
                errors.append({"path": str(root), "reason": "directory unavailable"})
                continue
            for path in root.glob("*.json"):
                rows.append(stamp(path))
        except OSError as exc:
            errors.append({"path": str(root), "reason": str(exc)[:200]})
    rows.sort(key=lambda r: (r["mtime_utc"], r["path"]), reverse=True)
    return {"evidence_kind": "saved_files_only", "live_solver_checked": False,
            "scope": folders, "sort": "mtime_desc_not_simulation_date", "total": len(rows),
            "items": rows[:limit], "omitted": max(0, len(rows) - limit), "errors": errors}


def pointer_value(value, pointer):
    if pointer and not pointer.startswith("/"):
        raise ValueError("JSON pointer must start with /, e.g. /metrics/temperature")
    for token in pointer.split("/")[1:] if pointer else []:
        key = token.replace("~1", "/").replace("~0", "~")
        if isinstance(value, list):
            if not key.isdecimal() or (key.startswith("0") and key != "0"):
                raise ValueError("invalid array index in pointer")
            value = value[int(key)]
        else:
            value = value[key]
    return value


def preview(value, limit, depth=0, budget=None):
    """Every omission is explicit; previews never imply full result validation."""
    budget = [48] if budget is None else budget
    budget[0] -= 1
    if budget[0] < 0:
        return {"preview_omitted": True}
    if isinstance(value, dict):
        keys = list(value)
        if depth >= 2:
            return {"kind": "object", "keys": keys[:limit], "total_keys": len(keys), "values_omitted": True}
        result = {"kind": "object", "values": {k: preview(value[k], limit, depth + 1, budget) for k in keys[:limit]},
                  "omitted_keys": len(keys) - min(limit, len(keys))}
        if depth == 0:
            result.update(available_keys=keys[:50], omitted_key_names=max(0, len(keys) - 50))
        return result
    if isinstance(value, list):
        count = min(limit, len(value)) if depth < 2 else 0
        return {"kind": "array", "length": len(value),
                "items": [preview(v, limit, depth + 1, budget) for v in value[:count]],
                "omitted_items": len(value) - count}
    if isinstance(value, str) and len(value) > 240:
        return {"text_prefix": value[:240], "omitted_characters": len(value) - 240}
    return value


def evidence(path, pointer, limit):
    if path.suffix.lower() != ".json":
        raise ValueError("evidence accepts .json summary files only")
    with path.open("rb") as stream:
        raw = stream.read(2 * 1024 * 1024 + 1)
    if len(raw) > 2 * 1024 * 1024:
        raise ValueError("summary exceeds 2 MiB; choose a smaller summary file")
    data = json.loads(raw.decode("utf-8-sig"), parse_constant=lambda x: x)
    selected = pointer_value(data, pointer)
    return {**stamp(path), "sha256": hashlib.sha256(raw).hexdigest(),
            "evidence_kind": "saved_json_only", "live_solver_checked": False,
            "pointer": pointer, "preview": preview(selected, limit),
            "interpretation": "Saved values, not solver qualification. Use --pointer for omitted fields."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=DEFAULT_REPO)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("snapshot", "stages", "artifacts", "evidence"):
        p = sub.add_parser(name)
        p.add_argument("--limit", type=int, default=8)
        if name == "snapshot":
            p.add_argument("--live", action="store_true", help="one read-only remote lookup; no fetch")
        elif name == "stages":
            p.add_argument("--chain")
            p.add_argument("--query", default="")
        elif name == "evidence":
            p.add_argument("path", type=Path, help="absolute or relative to --repo")
            p.add_argument("--pointer", default="")
    args = parser.parse_args()
    try:
        if not 1 <= args.limit <= 25:
            raise ValueError("--limit must be between 1 and 25")
        repo = args.repo.resolve()
        if args.command == "snapshot":
            result = snapshot(repo, args.live, args.limit)
        elif args.command == "stages":
            result = stages(repo, args.chain, args.query, args.limit)
        elif args.command == "artifacts":
            result = artifacts(repo, args.limit)
        else:
            path = args.path if args.path.is_absolute() else repo / args.path
            result = evidence(path.resolve(), args.pointer, args.limit)
        result["observed_at_utc"] = datetime.now(timezone.utc).isoformat()
        output = json.dumps(result, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        if len(output) > 16000:
            raise ValueError("output exceeds 16000 characters; narrow --query, --pointer or --limit")
        print(output)
        return 0
    except (OSError, ValueError, KeyError, IndexError, TypeError, RecursionError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)[:400]}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
