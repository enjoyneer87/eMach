"""Verify packaged bytes, without normalizing or repairing them during a check."""
import argparse
import hashlib
from pathlib import Path


def verify(root):
    failures = []
    count = 0
    for line in (root / 'MANIFEST.sha256').read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        digest, name = line.split(None, 1)
        name = name.lstrip('*')
        path = (root / name).resolve()
        if not path.is_relative_to(root.resolve()):
            failures.append((name, 'unsafe path'))
            continue
        count += 1
        if not path.is_file():
            failures.append((name, 'missing'))
        elif hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            failures.append((name, 'hash mismatch'))
    for name, reason in failures:
        print(f'FAIL {name}: {reason}')
    print(f'Manifest: {count} entries, {len(failures)} failures')
    return int(bool(failures))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    raise SystemExit(verify(ap.parse_args().root))
