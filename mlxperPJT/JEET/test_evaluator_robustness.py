"""No-solver checks for the matched-kernel evaluator comparison."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np

from run_evaluator_robustness import hybrid, KERNELS, SIGMA_80
from run_ref_only_field_pipeline import evaluate_hybrid
from acloss_ref_methods import mesh_b_vs_mcad as legacy


class EvaluatorContracts(unittest.TestCase):
    def test_against_existing_standalone_kernels(self):
        row = {'b2t_msq_sum': [.7, .09, .002], 'b2r_msq_sum': [.15, .03, .006]}
        funcs = {'uncapped_P24c6': lambda f, bt, br, w, h: legacy.prox_24(f, bt, br, w, h, 6),
                 'G2': legacy.prox_g2, 'G2_modified_delta': legacy.prox_g2_volpe_prime}
        with patch.object(legacy, 'SIGMA', SIGMA_80), patch.object(legacy, '_SIGMA_V', SIGMA_80):
            for kr in (1., 1.5, 2.):
                for speed in (2000., 4000., 8000., 16000.):
                    p = SimpleNamespace(speed_rpm=speed, current_rms=460.*kr)
                    old = evaluate_hybrid(row, p.current_rms, speed, kr)
                    self.assertEqual(hybrid(row, p, kr, 'capped_P24c6'), old['hybrid_kW'])
                    for name, fn in funcs.items():
                        value = fn(np.arange(1,4)*speed*4/60,
                                   np.array(row['b2t_msq_sum']), np.array(row['b2r_msq_sum']),
                                   3.711e-3*kr, 1.686e-3*kr)
                        expected = (8*value+old['skin_excess_W'])/1000
                        self.assertAlmostEqual(hybrid(row, p, kr, name)/expected, 1., places=12)

    def test_similarity_for_each_kernel(self):
        row = {'b2t_msq_sum': [.7, .09, .002], 'b2r_msq_sum': [.15, .03, .006]}
        for kernel in KERNELS:
            for kr in (1.5, 2.):
                donor = SimpleNamespace(speed_rpm=2000*kr**2, current_rms=460.)
                target = SimpleNamespace(speed_rpm=2000., current_rms=460.*kr)
                self.assertAlmostEqual(hybrid(row, target, kr, kernel)/hybrid(row, donor, 1., kernel),
                                       1., places=12)


if __name__ == '__main__':
    unittest.main()
