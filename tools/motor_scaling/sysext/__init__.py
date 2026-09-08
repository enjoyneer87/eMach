"""System-level extensions of the scaled-map motor model (thesis ch. 7 §시스템 확장).

inverter   VSI conduction/switching loss (port of tools/loss/PE/calcVSILoss.m) + rating-based module cost
voltage    DC-link voltage axis: rewind (turn scaling), inverter current, insulation-system discrete choice
gearbox    single-stage reducer loss law (Aroua et al., Mech. Mach. Theory 2023) — validity range guarded
process_cost  manufacturing-process cost layer (Domingues-Olavarría et al., IEEE TIA 2019, Table II)
"""
from . import inverter, voltage, gearbox, process_cost  # noqa: F401
