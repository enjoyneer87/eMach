"""Scientific contracts for M1, independent of proprietary field files."""
import unittest
from dataclasses import replace

import numpy as np

from run_ref_only_field_pipeline import (
    evaluate_hybrid, ref_row_for, transferred_dataset,
    AcLossDataset, AcLossPipeline,
)


def spectrum(current=460.0, phase=36.0):
    return {"current_A": current, "phase_deg": phase,
            "b2t_msq_sum": [4.0, 0.1, 0.2, 0.01],
            "b2r_msq_sum": [0.5, 0.02, 0.01, 0.001],
            "raw_sha256": "synthetic-no-truth"}


class RefOnlyFieldContracts(unittest.TestCase):
    def test_kernel_similarity_including_transition_and_skin(self):
        row = spectrum()
        for kr in (1.5, 2.0):
            for speed in (2000, 4000, 16000):
                donor = evaluate_hybrid(row, 460, speed * kr ** 2, 1)
                target = evaluate_hybrid(row, 460 * kr, speed, kr)
                for key in ("proximity_W", "skin_excess_W", "hybrid_kW"):
                    self.assertAlmostEqual(target[key] / donor[key], 1, places=12)

    def test_axial_length_scales_total_loss(self):
        base = evaluate_hybrid(spectrum(), 920, 16000, 2)
        longer = evaluate_hybrid(spectrum(), 920, 16000, 2, ka=1.7)
        self.assertAlmostEqual(longer["hybrid_kW"] / base["hybrid_kW"], 1.7, places=12)

    def test_rounding_match_and_missing_or_ambiguous_coordinates(self):
        rows = [spectrum(115.1)]
        row, err = ref_row_for(rows, 230.075, 36, 2)
        self.assertIsNone(err)
        self.assertEqual(row["current_A"], 115.1)
        self.assertIsNotNone(ref_row_for(rows, 250, 36, 2)[1])
        self.assertIsNotNone(ref_row_for(rows * 2, 230.075, 36, 2)[1])

    def test_target_deposited_hybrid_does_not_enter_ref_only_denominator(self):
        # Real dataset coordinates exercise the replacement path. The field
        # spectra are synthetic; no target field or target hybrid is needed.
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()):
            ds = AcLossPipeline().load_dataset("SC")
        rows = [spectrum(c, b) for c in (115.1, 230.0, 345.0, 460.0)
                for b in (0, 18, 36, 54, 72, 90)]
        ds2 = AcLossDataset([replace(p, hybrid_ac_kW=p.hybrid_ac_kW * 99,
                                    AF=p.AF / 99) for p in ds.points])
        first, _, err1 = transferred_dataset(ds, rows, 2)
        second, _, err2 = transferred_dataset(ds2, rows, 2)
        self.assertIsNone(err1)
        self.assertIsNone(err2)
        self.assertEqual(len(first), 96)
        np.testing.assert_array_equal(first.h_ac_arr, second.h_ac_arr)
        np.testing.assert_array_equal(first.af_arr, second.af_arr)
        missing, _, err = transferred_dataset(ds, rows[:-1], 2)
        self.assertIsNone(missing)
        self.assertIsNotNone(err)


if __name__ == "__main__":
    unittest.main()
