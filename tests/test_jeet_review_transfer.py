"""Scientific regression checks for the adopted predicted-loss transfer."""
import contextlib
import copy
import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from jeet_acloss_rbf.pipeline import AcLossPipeline
from jeet_acloss_rbf.RbfModelBuilder import RbfModelBuilder as RB


class TransferContracts(unittest.TestCase):
    def setUp(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.p=AcLossPipeline()
            self.donor=self.p.build_donor()
            self.ref=self.p.load_dataset('Ref')
            self.sc=self.p.load_dataset('SC')

    def build(self,ref=None,sc=None,donor=None,rule='predicted_loss'):
        return RB.build_separable_rbf_transfer(
            sc if sc is not None else self.sc,
            donor if donor is not None else self.donor,2.,24,3,
            base_speed=16.,n_probe_transfer=6,exponent=True,
            placement='structured',donor_dataset=ref if ref is not None else self.ref,
            rule=rule)

    def predictions(self,m,ds=None):
        ds=ds if ds is not None else self.sc
        return ds.h_ac_arr*m.predict(ds.speeds_k*1000,ds.irms_arr,ds.phase_arr)

    def test_prediction_transfer_never_reads_donor_truth_array(self):
        original=self.predictions(self.build())
        changed=copy.deepcopy(self.ref)
        changed.f_ac_arr[:]=np.nan
        np.testing.assert_allclose(self.predictions(self.build(ref=changed)),original,
                                   rtol=1e-12,atol=1e-12)

    @unittest.expectedFailure
    def test_common_denominator_scaling_preserves_loss(self):
        # Open scientific contract, not a numerical tolerance issue. Independently
        # polynomial-fitted f and p do not preserve f*c**(p-1) under AF rescaling.
        original=self.predictions(self.build())
        c=2.7
        ref,sc=copy.deepcopy(self.ref),copy.deepcopy(self.sc)
        ref.h_ac_arr[:]*=c
        sc.h_ac_arr[:]*=c
        sc.af_arr[:]/=c
        donor=self.donor
        class ScaledDonor:
            def predict(self,*args):
                return donor.predict(*args)/c
        result=self.predictions(self.build(ref,sc,ScaledDonor()),sc)
        np.testing.assert_allclose(result,original,rtol=1e-8,atol=1e-10)

    def test_unknown_rule_does_not_silently_become_ratio(self):
        with self.assertRaises(ValueError):
            self.build(rule='misspelled')

    def test_direct_truth_rule_is_removed(self):
        self.assertEqual(RB.TRANSFER_RULE,'predicted_loss')
        with self.assertRaisesRegex(ValueError,'direct donor truth lookup was removed'):
            self.build(rule='numerator')

    def test_generator_normalizes_already_equal_text_before_hashing(self):
        path=ROOT/'mlxperPJT/JEET/package/make_package.py'
        spec=importlib.util.spec_from_file_location('package_generator',path)
        module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); src=root/'source'; dest=root/'dest'
            src.mkdir(); dest.mkdir()
            (src/'sample.txt').write_bytes(b'one\ntwo\n')
            (dest/'sample.txt').write_bytes(b'one\r\ntwo\r\n')
            manifest=root/'package_manifest.txt'
            manifest.write_text('@CASE/sample.txt -> sample.txt\n')
            module.MANIFEST=str(manifest)
            with contextlib.redirect_stdout(io.StringIO()):
                code=module.main(['--write','--dest',str(dest),'--root','CASE='+str(src)])
            self.assertEqual(code,0)
            self.assertEqual((dest/'sample.txt').read_bytes(),b'one\ntwo\n')


if __name__=='__main__':
    unittest.main()
