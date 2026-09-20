"""Regression checks for data admission, missing evidence, and byte integrity."""
import contextlib
import io
import tempfile
import unittest
from pathlib import Path

import numpy as np

from jeet_acloss_rbf.pipeline import AcLossPipeline, DEFAULT_CONFIG
from jeet_acloss_rbf.form_study import region_mask, run_form_study
from scripts.check_manifest import verify


class ReviewContracts(unittest.TestCase):
    def test_relative_paths_and_admission(self):
        p=AcLossPipeline()
        with contextlib.redirect_stdout(io.StringIO()):
            for scale, relative in DEFAULT_CONFIG['json'].items():
                self.assertNotIn('\\',relative)
                self.assertFalse(Path(relative).is_absolute())
                self.assertEqual(len(p.load_dataset(scale)),96)

    def test_missing_operating_band_has_no_region_claim(self):
        from unittest.mock import patch
        p=AcLossPipeline()
        with contextlib.redirect_stdout(io.StringIO()), patch(
                'jeet_acloss_rbf.form_study.operating_beta_band',return_value={}):
            ds=p.load_dataset('Ref')
            self.assertFalse(region_mask(ds,{}).any())
            result=run_form_study(p,scales=('Ref',),n_seeds=1)
        self.assertEqual(result['meta']['operating_band_status'],'unavailable')
        self.assertIsNone(result['scales']['Ref']['uncorrected']['region_wmae'])
        for block in result['scales']['Ref']['placement'].values():
            for row in block['forms'].values():
                if row:
                    self.assertIsNone(row['region_wmae'])
                    self.assertTrue(np.isfinite(row['full_wmae']))

    def test_manifest_detects_changed_bytes(self):
        import hashlib
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/'sample.txt').write_bytes(b'line\n')
            digest=hashlib.sha256(b'line\n').hexdigest()
            (root/'MANIFEST.sha256').write_text(digest+'  sample.txt\n')
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(verify(root),0)
                (root/'sample.txt').write_bytes(b'line\r\n')
                self.assertEqual(verify(root),1)


if __name__=='__main__':
    unittest.main()
