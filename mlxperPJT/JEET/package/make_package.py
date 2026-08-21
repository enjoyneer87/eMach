# -*- coding: utf-8 -*-
"""Manifest-driven generator for the public reproduction package (JEET-repro).

Every file of the published package has its original in this worktree.  The
mapping lives in ``package_manifest.txt`` next to this script; this generator
either verifies an existing package tree against it (``--check``) or
(re)builds the tree from it (``--write [--prune]``).  Nothing is authored in
the destination by hand -- text files are copied with LF normalisation only,
binaries byte-for-byte.

Usage::

    python make_package.py --check --dest <package-dir> \
        [--root EMACH_E10=<path-to-eMach-e10>] \
        [--zenodo-manifest <zenodo_manifest.txt>]
    python make_package.py --write [--prune] --dest <package-dir> [...]

Root aliases usable on the left side of manifest entries:

==============  ==========================================================
``@TOOLS``      ``<worktree>/tools``
``@JEET``       ``<worktree>/mlxperPJT/JEET``
``@E10``        ``<worktree>/mlxperPJT/JEET/map_exports/e10``
``@PKG``        ``<worktree>/mlxperPJT/JEET/package`` (this directory)
``@EMACH_E10``  no default -- pass ``--root EMACH_E10=<path>`` (holds the
                efficiency-map ``.mat`` files too large for the worktree)
==============  ==========================================================

Per-file statuses:

``OK``               source and destination agree (text: after LF folding)
``STALE``            destination exists but differs from the source
``MISSING``          destination file absent
``NOSRC``            source file absent (another agent may still be writing
                     it, or a root alias was not given)
``LEAK``             source text matches the private-path pattern and the
                     entry is not flagged ``allow-abs``
``NB-OUTPUTS``       notebook still carries outputs / execution counts
``ZENODO-MISMATCH``  entry flagged ``zenodo-sha`` disagrees with the SHA-256
                     recorded in the Zenodo deposit manifest
``EXTRA``            file in the destination that no manifest entry produces

``--check`` exits 1 unless every entry is OK and nothing is EXTRA.
``--write`` copies everything it safely can (LEAK / NB-OUTPUTS /
ZENODO-MISMATCH sources are refused), then writes ``PROVENANCE.txt`` and
``MANIFEST.sha256``; ``--prune`` additionally deletes EXTRA files.
"""
from __future__ import annotations

import argparse
import fnmatch
import glob as _glob
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
# package/ -> JEET -> mlxperPJT -> worktree root
WORKTREE = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
MANIFEST = os.path.join(HERE, "package_manifest.txt")

ZENODO_DOI = "10.5281/zenodo.21775297"

#: private-path leak pattern (drive letters, the author's tree names, the
#: Korean Google Drive mount).  Checked on packaged *text* sources only.
LEAK_RE = re.compile(r"[A-Z]:[\\/]|KangDH|\bKDH\b|내 드라이브")

TEXT_EXTS = {".py", ".md", ".txt", ".m", ".cff", ".json", ".ipynb",
             ".yml", ".yaml", ".toml", ".cfg", ".gitignore", ".gitattributes"}

#: destination paths (relative, posix) never reported as EXTRA: metadata the
#: generator itself writes, VCS/tool litter, and files the packaged
#: ``.gitignore`` declares as run-time products.
EXTRA_SKIP_FILES = {"MANIFEST.sha256", "PROVENANCE.txt",
                    "data/e10/flux_torque_scaling_metrics.json",
                    "data/e10/SC/open_denominator_refit.json"}
EXTRA_SKIP_DIRS = {".git", "__pycache__", ".ipynb_checkpoints", "fig_out"}
EXTRA_SKIP_PREFIXES = ("data/e10/fea/", "data/e10/results/")

VALID_FLAGS = {"allow-abs", "no-outputs", "zenodo-sha"}


def is_text(path: str) -> bool:
    base = os.path.basename(path)
    ext = os.path.splitext(base)[1].lower()
    return ext in TEXT_EXTS or base in (".gitignore", ".gitattributes",
                                        "LICENSE", "CITATION.cff")


def lf_fold(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_bytes(path: str) -> bytes:
    with open(path, "rb") as fh:
        return fh.read()


def leak_hits(path: str, data: bytes):
    """Private-path pattern hits in one text file.

    Notebooks are scanned on their JSON-decoded strings: in raw ``.ipynb``
    text a code line ending in an upper-case letter plus colon is followed
    by the *escaped* newline ``\\n``, which fakes a drive letter (``R:\\``
    out of ``ORDER:``).  Decoding restores real newlines first; genuine
    drive letters survive the decode and are still caught.
    """
    if path.endswith(".ipynb"):
        try:
            nb = json.loads(data.decode("utf-8"))
        except Exception:                          # noqa: BLE001
            return LEAK_RE.findall(data.decode("utf-8", errors="replace"))
        hits = []

        def walk(obj):
            if isinstance(obj, str):
                hits.extend(LEAK_RE.findall(obj))
            elif isinstance(obj, dict):
                for v in obj.values():
                    walk(v)
            elif isinstance(obj, list):
                for v in obj:
                    walk(v)
        walk(nb)
        return hits
    return LEAK_RE.findall(data.decode("utf-8", errors="replace"))


def notebook_has_outputs(path: str):
    """True / False, or a string describing a parse failure."""
    try:
        nb = json.loads(read_bytes(path).decode("utf-8"))
    except Exception as exc:                      # noqa: BLE001 - report it
        return "unparseable notebook (%s)" % exc
    for cell in nb.get("cells", []):
        if cell.get("outputs") or cell.get("execution_count") is not None:
            return True
    return False


# ── manifest ──────────────────────────────────────────────────────────────

class Entry:
    __slots__ = ("src", "dest", "flags", "line")

    def __init__(self, src, dest, flags, line):
        self.src, self.dest, self.flags, self.line = src, dest, flags, line


def parse_manifest(path: str):
    entries = []
    with open(path, encoding="utf-8") as fh:
        for ln, raw in enumerate(fh, 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "->" not in line:
                sys.exit("manifest line %d: no '->': %s" % (ln, line))
            src, rest = (s.strip() for s in line.split("->", 1))
            flags = set()
            m = re.search(r"\[([^\]]*)\]\s*$", rest)
            if m:
                flags = {f.strip() for f in m.group(1).split(",") if f.strip()}
                rest = rest[:m.start()].strip()
            bad = flags - VALID_FLAGS
            if bad:
                sys.exit("manifest line %d: unknown flag(s) %s" %
                         (ln, ", ".join(sorted(bad))))
            entries.append(Entry(src, rest, flags, ln))
    return entries


def resolve_roots(overrides):
    roots = {
        "TOOLS": os.path.join(WORKTREE, "tools"),
        "JEET": os.path.join(WORKTREE, "mlxperPJT", "JEET"),
        "E10": os.path.join(WORKTREE, "mlxperPJT", "JEET",
                            "map_exports", "e10"),
        "PKG": HERE,
        "EMACH_E10": None,
    }
    for ov in overrides or []:
        if "=" not in ov:
            sys.exit("--root wants NAME=PATH, got: %s" % ov)
        name, val = ov.split("=", 1)
        roots[name.strip()] = os.path.abspath(val.strip())
    return roots


def expand_entry(entry, roots):
    """-> (root_ok, [(src_abs_or_None, dest_rel)], note).

    A glob source maps every match into the destination directory by
    basename.  A glob with no match yields one NOSRC record for the pattern.
    """
    src = entry.src
    if not src.startswith("@"):
        return False, [], "source must start with a @ROOT alias"
    alias, _, rel = src[1:].partition("/")
    if alias not in roots:
        return False, [], "unknown root @%s" % alias
    base = roots[alias]
    if base is None:
        return False, [], ("root @%s not set -- pass --root %s=<path>"
                           % (alias, alias))
    rel = rel.replace("/", os.sep)
    pattern = os.path.normpath(os.path.join(base, rel))
    is_dir_dest = entry.dest.endswith("/")

    if any(ch in rel for ch in "*?["):
        if not is_dir_dest:
            return False, [], "glob source needs a directory destination"
        matches = sorted(p for p in
                         _glob.glob(pattern, recursive=True)
                         if os.path.isfile(p)
                         and "__pycache__" not in p
                         and not p.endswith(".pyc"))
        if not matches:
            return True, [(None, entry.dest + os.path.basename(rel))], \
                "glob matched nothing: %s" % entry.src
        return True, [(m, entry.dest + os.path.basename(m))
                      for m in matches], None

    dest_rel = (entry.dest + os.path.basename(pattern)) if is_dir_dest \
        else entry.dest
    return True, [(pattern, dest_rel)], None


# ── zenodo manifest ───────────────────────────────────────────────────────

def load_zenodo_manifest(path):
    """basename -> sha256 from a ``sha  size  relpath`` listing."""
    table = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 3 or len(parts[0]) != 64:
                continue
            table[os.path.basename(parts[-1])] = parts[0]
    return table


# ── per-file check ────────────────────────────────────────────────────────

def check_one(src, dest_abs, flags, zenodo, zenodo_given):
    """-> (statuses, notes) for one src -> dest pair."""
    statuses, notes = [], []
    if src is None or not os.path.isfile(src):
        statuses.append("NOSRC")
        if dest_abs and os.path.isfile(dest_abs):
            notes.append("destination exists but has no source")
        return statuses, notes

    data = read_bytes(src)
    text = is_text(src)

    if text and "allow-abs" not in flags:
        hits = leak_hits(src, data)
        if hits:
            statuses.append("LEAK")
            uniq = sorted(set(hits))
            notes.append("%d hit(s): %s" % (len(hits), ", ".join(uniq[:4])))

    if src.endswith(".ipynb") or "no-outputs" in flags:
        has = notebook_has_outputs(src)
        if has:
            statuses.append("NB-OUTPUTS")
            if isinstance(has, str):
                notes.append(has)

    if "zenodo-sha" in flags:
        if not zenodo_given:
            notes.append("zenodo-sha not verified (no --zenodo-manifest)")
        else:
            want = zenodo.get(os.path.basename(src))
            got = sha256_bytes(data)
            if want is None:
                statuses.append("ZENODO-MISMATCH")
                notes.append("not in the deposit manifest")
            elif want != got:
                statuses.append("ZENODO-MISMATCH")
                notes.append("deposit %s.. != source %s.." %
                             (want[:12], got[:12]))

    if not os.path.isfile(dest_abs):
        statuses.append("MISSING")
    else:
        want = lf_fold(data) if text else data
        have = read_bytes(dest_abs)
        if text:
            have = lf_fold(have)
        if sha256_bytes(want) != sha256_bytes(have):
            statuses.append("STALE")

    return statuses, notes


# ── write helpers ─────────────────────────────────────────────────────────

def write_one(src, dest_abs):
    data = read_bytes(src)
    if is_text(src):
        data = lf_fold(data)
    os.makedirs(os.path.dirname(dest_abs) or ".", exist_ok=True)
    with open(dest_abs, "wb") as fh:
        fh.write(data)
    return data


def git_provenance():
    def run(*args):
        try:
            out = subprocess.run(["git", "-C", WORKTREE] + list(args),
                                 capture_output=True, text=True, timeout=30)
            return out.stdout.strip() if out.returncode == 0 else ""
        except OSError:
            return ""
    head = run("rev-parse", "HEAD") or "(unknown)"
    dirty = bool(run("status", "--porcelain"))
    return head, dirty


def scan_extra(dest, produced):
    extra = []
    for root, dirs, files in os.walk(dest):
        dirs[:] = [d for d in dirs if d not in EXTRA_SKIP_DIRS]
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), dest)
            rel = rel.replace(os.sep, "/")
            if rel in EXTRA_SKIP_FILES or rel in produced:
                continue
            if any(rel.startswith(p) for p in EXTRA_SKIP_PREFIXES):
                continue
            extra.append(rel)
    return sorted(extra)


# ── main ──────────────────────────────────────────────────────────────────

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Verify or build the JEET-repro package from "
                    "package_manifest.txt.")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true",
                      help="report per-file status; exit 1 unless all OK")
    mode.add_argument("--write", action="store_true",
                      help="copy sources into --dest, then write "
                           "PROVENANCE.txt and MANIFEST.sha256")
    ap.add_argument("--dest", required=True,
                    help="package root directory (no default on purpose)")
    ap.add_argument("--prune", action="store_true",
                    help="with --write: delete EXTRA files from --dest")
    ap.add_argument("--root", action="append", metavar="NAME=PATH",
                    help="set or override a root alias")
    ap.add_argument("--zenodo-manifest", metavar="PATH",
                    help="deposit listing (sha256  size  name) used by "
                         "entries flagged zenodo-sha")
    a = ap.parse_args(argv)

    dest = os.path.abspath(a.dest)
    roots = resolve_roots(a.root)
    entries = parse_manifest(MANIFEST)

    zenodo, zenodo_given = {}, False
    if a.zenodo_manifest:
        zenodo = load_zenodo_manifest(a.zenodo_manifest)
        zenodo_given = True
        print("[info] zenodo manifest: %d entries from %s"
              % (len(zenodo), a.zenodo_manifest))
    elif any("zenodo-sha" in e.flags for e in entries):
        print("[warn] entries flagged zenodo-sha are NOT verified "
              "(no --zenodo-manifest given)")

    rows = []           # (statuses, dest_rel, notes, src_abs, flags)
    produced = set()
    seen_dest = {}
    for e in entries:
        ok, pairs, note = expand_entry(e, roots)
        if not ok:
            rows.append((["NOSRC"], e.dest, [note], None, e.flags))
            continue
        for src_abs, dest_rel in pairs:
            dest_rel = dest_rel.replace(os.sep, "/")
            if dest_rel in seen_dest:
                rows.append((["NOSRC"], dest_rel,
                             ["duplicate destination (lines %d and %d)"
                              % (seen_dest[dest_rel], e.line)],
                             None, e.flags))
                continue
            seen_dest[dest_rel] = e.line
            produced.add(dest_rel)
            st, notes = check_one(src_abs, os.path.join(dest, dest_rel),
                                  e.flags, zenodo, zenodo_given)
            if note:
                notes = [note] + notes
            rows.append((st, dest_rel, notes, src_abs, e.flags))

    # ── write pass ────────────────────────────────────────────────────
    if a.write:
        written = 0
        for i, (st, dest_rel, notes, src_abs, flags) in enumerate(rows):
            blocking = {"NOSRC", "LEAK", "NB-OUTPUTS", "ZENODO-MISMATCH"}
            if set(st) & blocking:
                continue
            if st:                                # MISSING / STALE only
                write_one(src_abs, os.path.join(dest, dest_rel))
                written += 1
                rows[i] = ([], dest_rel, notes, src_abs, flags)
        print("[write] %d file(s) copied into %s" % (written, dest))

    extra = scan_extra(dest, produced) if os.path.isdir(dest) else []
    if a.write and a.prune:
        for rel in extra:
            path = os.path.join(dest, rel)
            os.remove(path)
            print("[prune] removed %s" % rel)
            d = os.path.dirname(path)
            while d != dest and os.path.isdir(d) and not os.listdir(d):
                os.rmdir(d)
                d = os.path.dirname(d)
        extra = []

    if a.write:
        copied = [(r[1], os.path.join(dest, r[1]))
                  for r in rows if not r[0]]
        total = sum(os.path.getsize(p) for _, p in copied)
        head, dirty = git_provenance()
        prov = os.path.join(dest, "PROVENANCE.txt")
        with open(prov, "wb") as fh:
            fh.write(("JEET-repro package provenance\n"
                      "generated-by: mlxperPJT/JEET/package/make_package.py\n"
                      "source-repo: enjoyneer87/eMach (branch devVeriACLoss)\n"
                      "source-commit: %s%s\n"
                      "generated-utc: %s\n"
                      "files: %d\n"
                      "total-bytes: %d\n"
                      "zenodo-dataset: %s\n"
                      % (head, " (dirty)" if dirty else "",
                         datetime.now(timezone.utc)
                         .strftime("%Y-%m-%dT%H:%M:%SZ"),
                         len(copied), total, ZENODO_DOI)).encode("utf-8"))
        man = os.path.join(dest, "MANIFEST.sha256")
        with open(man, "wb") as fh:
            for rel, path in sorted(copied) + [("PROVENANCE.txt", prov)]:
                fh.write(("%s  %s\n" % (sha256_bytes(read_bytes(path)),
                                        rel)).encode("utf-8"))
        print("[write] PROVENANCE.txt + MANIFEST.sha256 "
              "(%d files, %d bytes)" % (len(copied), total))

    # ── report ────────────────────────────────────────────────────────
    counts = {}
    for st, dest_rel, notes, _src, _fl in rows:
        label = "+".join(st) if st else "OK"
        counts[label] = counts.get(label, 0) + 1
        if st:
            note = ("  (" + "; ".join(notes) + ")") if notes else ""
            print("%-18s %s%s" % (label, dest_rel, note))
    for rel in extra:
        counts["EXTRA"] = counts.get("EXTRA", 0) + 1
        print("%-18s %s" % ("EXTRA", rel))

    print("-" * 60)
    print("  ".join("%s:%d" % kv for kv in sorted(counts.items())))
    bad = sum(v for k, v in counts.items() if k != "OK")
    if bad:
        print("[fail] %d file(s) not OK" % bad)
        return 1
    print("[ok] all %d files match the manifest" % counts.get("OK", 0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
