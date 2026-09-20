"""Transfer must consume the fitted donor, never withheld donor Full-FEA."""
import contextlib
import copy
import io
import unittest

import numpy as np

from jeet_acloss_rbf.pipeline import AcLossPipeline
from jeet_acloss_rbf.RbfModelBuilder import RbfModelBuilder as RB
from jeet_acloss_rbf.cost_accuracy import sweep_cost_accuracy


class TransferBudget(unittest.TestCase):
    def test_fixed_coordinates_match_default_and_reject_invalid_plan(self):
        with contextlib.redirect_stdout(io.StringIO()):
            p = AcLossPipeline()
            donor, ref, ds = p.build_donor(), p.load_dataset('Ref'), p.load_dataset('SC')
            expected = p.build_model('SC')
            expected_train = RB.last_train_idx.copy()
            probes = RB.plan_sampling_indices(ds, 24, 6, base_speed=16., placement='structured')
            own = RB.plan_sampling_indices(ds, 24, 3, base_speed=16., placement='structured')
        plan = {'base': probes['base'], 'by_speed': dict(probes['by_speed'])}
        plan['by_speed'][8.] = own['by_speed'][8.]
        def fit(ip):
            return RB.build_separable_rbf_transfer(
                ds, donor, 2., 24, 3, base_speed=16., n_probe_transfer=6,
                exponent=True, placement='structured', donor_dataset=ref, index_plan=ip)
        actual = fit(plan)
        np.testing.assert_array_equal(RB.last_train_idx, expected_train)
        args = (ds.speeds_k*1000, ds.irms_arr, ds.phase_arr)
        np.testing.assert_allclose(actual.predict(*args), expected.predict(*args), rtol=1e-13)
        for kind in ('missing_speed', 'duplicate_index', 'wrong_speed'):
            bad = copy.deepcopy(plan)
            if kind == 'missing_speed':
                del bad['by_speed'][2.]
            elif kind == 'duplicate_index':
                bad['by_speed'][8.][1] = bad['by_speed'][8.][0]
            else:
                bad['by_speed'][8.][0] = bad['base'][0]
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                fit(bad)

    def test_default_transfer_accepts_hybrid_only_donor(self):
        with contextlib.redirect_stdout(io.StringIO()):
            p=AcLossPipeline()
            donor=p.build_donor()
            ref=p.load_dataset('Ref')
            ds=p.load_dataset('SC')
            expected=p.build_model('SC')

        class HybridOnly:
            # Deliberately has neither f_ac_arr nor af_arr.
            speeds_k=ref.speeds_k
            irms_arr=ref.irms_arr
            phase_arr=ref.phase_arr
            h_ac_arr=ref.h_ac_arr

        actual=RB.build_separable_rbf_transfer(
            ds,donor,2.,24,3,base_speed=16.,n_probe_transfer=6,
            exponent=True,placement='structured',donor_dataset=HybridOnly())
        args=(ds.speeds_k*1000,ds.irms_arr,ds.phase_arr)
        np.testing.assert_allclose(actual.predict(*args),expected.predict(*args),rtol=1e-12)
        self.assertEqual(RB.TRANSFER_RULE,'predicted_loss')

    def test_pipeline_never_uses_unselected_ref_truth(self):
        with contextlib.redirect_stdout(io.StringIO()):
            baseline=AcLossPipeline()
            baseline.build_donor()
            train=RB.last_train_idx.copy()
            expected=baseline.build_model('SC')
            ds=baseline.load_dataset('SC')
            p=AcLossPipeline()
            ref=p.load_dataset('Ref')
            withheld=~np.isin(np.arange(len(ref)),train)
            ref.f_ac_arr[withheld]=np.nan
            ref.af_arr[withheld]=np.nan
            actual=p.build_model('SC')
        self.assertEqual(len(train),36)
        self.assertEqual(int(withheld.sum()),60)
        np.testing.assert_allclose(
            actual.predict(ds.speeds_k*1000,ds.irms_arr,ds.phase_arr),
            expected.predict(ds.speeds_k*1000,ds.irms_arr,ds.phase_arr),rtol=1e-12)

    def test_ablation_and_cost_use_the_same_transfer(self):
        with contextlib.redirect_stdout(io.StringIO()):
            p=AcLossPipeline()
            expected=p.metrics('SC')['wmae_pct']
            ablation=p.transfer_ablation_grid('SC',[24],[3],1,'structured')
            cost=sweep_cost_accuracy(p,scales=('SC',),budgets=(27,),
                n_spd_list=(3,),modes=('transfer',),placements=('structured',),n_seeds=1)
        self.assertAlmostEqual(float(ablation['wmae_pct'][0,0]),expected,places=10)
        runs=cost['scales']['SC']['runs']
        self.assertEqual(len(runs),1)
        self.assertAlmostEqual(runs[0]['wmae'],expected,places=10)


if __name__=='__main__':
    unittest.main()
