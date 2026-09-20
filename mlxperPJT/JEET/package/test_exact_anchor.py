"""Speed constraints, independent constrained optimum, and exported formulas."""
import contextlib
import io
import unittest
from dataclasses import replace

import numpy as np

from jeet_acloss_rbf.RbfModelBuilder import RbfModelBuilder as RB
from jeet_acloss_rbf.pipeline import AcLossPipeline


class ExactAnchor(unittest.TestCase):
    def test_constrained_optimum_at_arbitrary_base(self):
        # Independent KKT solution in the unshifted polynomial basis.
        for base in (2., 16., 27.5):
            s = base * np.array([.125, .25, .5, 1.])
            y = np.array([.55, .78, .91, 1.])
            coeff = RB._anchored_quadratic(s, y, base)
            v = np.vander(s, 3)
            c = np.array([base**2, base, 1.])
            kkt = np.block([[v.T@v, c[:, None]], [c[None, :], np.zeros((1, 1))]])
            optimum = np.linalg.solve(kkt, np.r_[v.T@y, 1.])[:3]
            np.testing.assert_allclose(v@coeff, v@optimum, atol=1e-11, rtol=1e-11)
            self.assertAlmostEqual(float(c@coeff), 1., places=13)
            self.assertGreater(abs(float(c@np.polyfit(s, y, 2))-1.), .001)

    def test_sparse_and_scalar_speed_fits(self):
        f, p = RB._fit_speed_scaling({}, 16., False, False)
        np.testing.assert_array_equal(f, [0., 0., 1.])
        self.assertIsNone(p)
        f, p = RB._fit_speed_scaling({8.: [(1.6, 2.)]}, 16., True, False)
        self.assertAlmostEqual(np.polyval(f, 8.), .8, places=13)
        for q in (f, p):
            self.assertAlmostEqual(np.polyval(q, 16.), 1., places=13)
        with self.assertRaises(ValueError):
            RB._anchored_quadratic([0.], [1.], 0.)

    def test_full_pipeline_preserves_base_shape_and_exported_anchor(self):
        with contextlib.redirect_stdout(io.StringIO()):
            pipeline = AcLossPipeline()
            for scale, expected in [('Ref', .6130499486),
                                    ('HalfSC', .8148335520171746), ('SC', .7165873461911869)]:
                model = pipeline.build_model(scale)
                ds = pipeline.load_dataset(scale)
                g = model.predict_g(ds.irms_arr, ds.phase_arr)
                np.testing.assert_allclose(model.predict(16000., ds.irms_arr, ds.phase_arr),
                                           g, rtol=1e-13, atol=1e-13)
                self.assertAlmostEqual(pipeline.metrics(scale)['wmae_pct'], expected, places=7)
                # Compare serialized f,p with constant f=p=1. The same rounded
                # RBF appears on both sides, isolating the export speed constraint.
                constant = replace(model, p_coeffs=np.array([0., 0., 1.]),
                                   q_coeffs=np.array([0., 0., 1.]))
                env = {'Speed': 16000., 'Stator_Current_Phase_RMS': float(ds.irms_arr[-1]),
                       'Phase_Advance': float(ds.phase_arr[-1]),
                       'Stator_Copper_Loss_AC': 1., 'log': np.log}
                self.assertEqual(eval(model.mcad_formula, {'__builtins__': {}}, env),
                                 eval(constant.mcad_formula, {'__builtins__': {}}, env))


if __name__ == '__main__':
    unittest.main()
