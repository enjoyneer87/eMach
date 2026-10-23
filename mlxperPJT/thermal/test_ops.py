"""Contract checks in temporary repositories, without any engineering runtime."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("emach_ops", Path(__file__).with_name("ops.py"))
ops = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ops)


class OpsTests(unittest.TestCase):
    def test_git_names_and_rename(self):
        out = ops.changes("R  new file.py\0old.py\0?? 한글.txt\0 M other.py\0UU conflict.py\0", 2)
        self.assertEqual(out["counts"]["files"], 4)
        self.assertEqual(out["counts"]["conflicts"], 1)
        self.assertEqual(out["omitted_paths"], 2)
        self.assertEqual(out["paths"][1]["path"], "한글.txt")

    def test_saved_failure_zero_and_pointer(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.json"
            path.write_text(json.dumps({"status": "failed", "power": 0, "ok": False, "a/b": {"~k": [42]}}))
            out = ops.evidence(path, "", 8)
            self.assertEqual(out["preview"]["values"]["status"], "failed")
            self.assertIs(out["preview"]["values"]["ok"], False)
            self.assertEqual(out["preview"]["values"]["power"], 0)
            self.assertFalse(out["live_solver_checked"])
            self.assertEqual(ops.evidence(path, "/a~1b/~0k/0", 8)["preview"], 42)

    def test_omissions_and_limit(self):
        out = ops.preview(list(range(100)), 3)
        self.assertEqual(out["omitted_items"], 97)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "large.json"
            path.write_bytes(b" " * (2 * 1024 * 1024 + 1))
            with self.assertRaises(ValueError):
                ops.evidence(path, "", 8)
            path.write_text("not JSON")
            with self.assertRaises(ValueError):
                ops.evidence(path, "", 8)

    def test_registry_reuse(self):
        module = ops.registry(ops.DEFAULT_REPO)
        result = ops.stages(ops.DEFAULT_REPO, "e10", "mapdl", 2)
        expected = [s for s in module.STAGES if s.chain == "e10" and "mapdl" in
                    " ".join((s.id, s.tool, s.desc, s.script)).casefold()]
        self.assertEqual(result["total"], len(expected))
        self.assertLessEqual(len(result["items"]), 2)
        self.assertEqual(result["items"][0]["id"], expected[0].id)

    def test_git_live_stale_cache_and_uncommitted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            remote, local = root / "remote.git", root / "local"

            def run(*args):
                return subprocess.check_output(["git", *map(str, args)], stderr=subprocess.DEVNULL).decode().strip()

            run("init", "--bare", remote)
            run("init", "-b", "main", local)
            run("-C", local, "config", "user.name", "fixture")
            run("-C", local, "config", "user.email", "fixture@example.invalid")
            (local / "tracked").write_text("base")
            run("-C", local, "add", "tracked")
            run("-C", local, "commit", "-m", "base")
            run("-C", local, "remote", "add", "origin", remote)
            run("-C", local, "push", "-u", "origin", "main")
            (local / "AGENTS.md").write_text("preserve me")
            before = (local / ".git/index").read_bytes()
            result = ops.snapshot(local, True, 8)
            self.assertEqual(result["remote"]["relation"], "identical")
            self.assertEqual(result["changes"]["counts"]["untracked"], 1)
            self.assertEqual(before, (local / ".git/index").read_bytes())
            (local / "tracked").write_text("next")
            run("-C", local, "commit", "-am", "next")
            self.assertEqual(ops.snapshot(local, True, 8)["remote"]["relation"], "local_ahead")
            run("-C", local, "push")
            run("-C", local, "reset", "--hard", "HEAD~1")  # Only this temporary fixture.
            self.assertEqual(ops.snapshot(local, True, 8)["remote"]["relation"], "local_behind")
            other = root / "other"
            run("clone", "--branch", "main", remote, other)
            run("-C", other, "config", "user.name", "fixture")
            run("-C", other, "config", "user.email", "fixture@example.invalid")
            (other / "tracked").write_text("external")
            run("-C", other, "commit", "-am", "external")
            run("-C", other, "push")
            self.assertEqual(ops.snapshot(local, True, 8)["remote"]["relation"], "unknown")
            self.assertEqual((local / "AGENTS.md").read_text(), "preserve me")


if __name__ == "__main__":
    unittest.main()
