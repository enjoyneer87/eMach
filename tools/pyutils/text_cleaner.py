from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


DEFAULT_BAD_CHARS: tuple[str, ...] = ("\uFFFD",)


def clean_text(text: str, bad_chars: Sequence[str] = DEFAULT_BAD_CHARS) -> str:
    for ch in bad_chars:
        if ch:
            text = text.replace(ch, "")
    return text


@dataclass(frozen=True)
class FixResult:
    path: Path
    changed: bool


def fix_file(
    path: Path,
    *,
    bad_chars: Sequence[str] = DEFAULT_BAD_CHARS,
    encoding: str = "utf-8",
    decode_errors: str = "replace",
) -> FixResult:
    try:
        raw = path.read_bytes()
        text = raw.decode(encoding, errors=decode_errors)
    except Exception:
        return FixResult(path=path, changed=False)

    new_text = clean_text(text, bad_chars=bad_chars)
    if new_text == text:
        return FixResult(path=path, changed=False)

    path.write_text(new_text, encoding=encoding)
    return FixResult(path=path, changed=True)


def fix_tree(
    root: Path,
    *,
    glob: str = "*.py",
    bad_chars: Sequence[str] = DEFAULT_BAD_CHARS,
    encoding: str = "utf-8",
    decode_errors: str = "replace",
    dry_run: bool = False,
) -> int:
    root = Path(root)
    fixed = 0

    for file_path in root.rglob(glob):
        if not file_path.is_file():
            continue

        if dry_run:
            try:
                raw = file_path.read_bytes()
                text = raw.decode(encoding, errors=decode_errors)
            except Exception:
                continue
            if clean_text(text, bad_chars=bad_chars) != text:
                fixed += 1
            continue

        result = fix_file(file_path, bad_chars=bad_chars, encoding=encoding, decode_errors=decode_errors)
        if result.changed:
            fixed += 1

    return fixed


def _iter_bad_chars(values: Iterable[str] | None) -> tuple[str, ...]:
    if not values:
        return DEFAULT_BAD_CHARS
    out: list[str] = []
    for v in values:
        if v is None:
            continue
        v = str(v)
        if v:
            out.append(v)
    return tuple(out) if out else DEFAULT_BAD_CHARS


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Remove problematic characters from files under a folder")
    parser.add_argument("root", type=str, help="Root folder to scan")
    parser.add_argument("--glob", default="*.py", help="Glob to match (default: *.py)")
    parser.add_argument("--bad-char", action="append", dest="bad_chars")
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args(argv)

    root = Path(args.root)
    bad_chars = _iter_bad_chars(args.bad_chars)

    fixed = fix_tree(root, glob=args.glob, bad_chars=bad_chars, dry_run=bool(args.dry_run))

    if args.dry_run:
        print(f"Dry-run: {fixed} file(s) would be changed.")
    else:
        print(f"Done. Fixed {fixed} file(s).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
