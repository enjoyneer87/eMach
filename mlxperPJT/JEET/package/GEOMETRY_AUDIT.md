# Physical airgap correction, 2026-09-20

The model parameters are Ref / HalfSC / SC airgaps of 1.0 / 1.5 / 2.0 mm.
The corresponding rotor diameters are 140.54 / 210.81 / 281.08 mm and stator
bore diameters are 142.54 / 213.81 / 285.08 mm. The airgap is half the
difference between bore and rotor diameters.

The previous DXF figure generator selected the moving-band sector envelope
as the rotor surface. Its radius is approximately 70.77 mm, whereas the
physical reference rotor radius is 70.27 mm. That produced the incorrect
printed reference airgap of 0.5 mm and rotor diameter of approximately
141.5 mm. The simulations inspected use the physical airgap of 1.0 mm.

The corrected selector excludes origin-crossing sector envelopes from the
annular material candidates. This rule targets the deposited Motor-CAD DXF
format. It is not a universal material classifier for arbitrary DXF files.
A missing annular candidate produces an explicit error.

The regression test reads the deposited DXF and checks the generated
dimensions against the physical model values. Run

```sh
python -m unittest discover -s tests -p 'test_geometry_airgap.py' -v
```

The author-side audit also checks current archived model files and the
airgap nodes of six selected Hybrid/FullFEA exports across the three
machines. The model gap ratios are exactly 1 / 1.5 / 2. Export boundary
differences fall within the 0.001 mm coordinate-rounding precision.
This is not an audit of every operating point or every model revision.

The correction changes geometry reporting, not the stored loss data or
calibration arrays. Existing manually annotated manuscript figures are not
overwritten. A revised manuscript must select the corrected generated figure
or update its annotated copy separately.
