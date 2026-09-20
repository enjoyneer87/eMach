"""The moving-band envelope must not become the physical rotor surface."""
from pathlib import Path
import tempfile
import unittest

from jeet_acloss_rbf.manuscript_figs import plot_motor_geometry_dxf


class PhysicalAirgap(unittest.TestCase):
    def test_deposited_dxf_uses_physical_rotor_boundary(self):
        dxf = Path(__file__).resolve().parents[1] / 'data/e10/e10_2d.dxf'
        self.assertTrue(dxf.is_file())
        with tempfile.TemporaryDirectory() as folder:
            dims = plot_motor_geometry_dxf(str(dxf), str(Path(folder) / 'geometry.pdf'))
        self.assertAlmostEqual(dims['Dr_mm'], 140.54, delta=.002)
        self.assertAlmostEqual(dims['g_mm'], 1.0, delta=.002)
        self.assertAlmostEqual(dims['Ds_mm'], 198.0, delta=.002)


if __name__ == '__main__':
    unittest.main()
