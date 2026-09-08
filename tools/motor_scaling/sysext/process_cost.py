# -*- coding: utf-8 -*-
"""Manufacturing-process cost layer (Domingues-Olavarría et al., IEEE TIA 55(1), 2019, eqs. 14–16 and Table II).

k(x, N) = K_A/N + K_B/(1-q_Q) + K_CP t_0/(1-q_Q) + K_CS t_0 q_s/((1-q_Q)(1-q_s)) + K_D t_0/((1-q_Q)(1-q_s))

Table II gives *ranges* per process (tool investment kEUR, cycle time s, personnel, operating cost EUR/h, yield %).
This module evaluates the per-unit process cost from the range midpoints (or lo/hi) with explicit assumptions:
annual volume N, wage EUR/h (personnel × wage = K_D), stop fraction q_s, tool amortisation over ``years``.
Materials (K_B) are *not* included here — they are the thesis' material layer (ipmfea.cost).
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

TABLE_CSV = Path(__file__).with_name("lund_tia2019_table2.csv")

#: processes that act on the active part (stator/rotor stack, winding, magnets); the rest is housing/assembly
ACTIVE_PART = ("Blanking", "Stacking", "Slot insulation", "Insertion winding", "Terminate and stitch",
               "Trickle coat", "Insulation test", "Magnet insertion", "Magnetization")


def load_table(path: Path = TABLE_CSV) -> List[Dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append({k: (float(v) if v not in ("", None) else None) if k != "process" else v for k, v in r.items()})
    return rows


@dataclass
class ProcessCostModel:
    volume_per_year: float = 50_000.0      # paper's case
    years: float = 1.0                     # tooling amortisation horizon used for K_A/N (paper: N per year)
    wage_eur_h: float = 35.0               # assumption (Eurostat 2018 manufacturing wage, W. Europe)
    q_s: float = 0.05                      # stop fraction (assumption)
    eur_to_usd: float = 1.10
    which: str = "mid"                     # "lo" | "mid" | "hi"

    def _v(self, row, key):
        lo, hi = row[key + "_lo"], row[key + "_hi"]
        if lo is None and hi is None:
            return None
        lo = hi if lo is None else lo; hi = lo if hi is None else hi
        return {"lo": lo, "hi": hi, "mid": 0.5 * (lo + hi)}[self.which]

    def per_unit(self, processes=None) -> Dict[str, float]:
        """EUR per unit for each process (and 'total'); materials excluded."""
        out = {}
        N = self.volume_per_year * self.years
        for r in load_table():
            if processes and r["process"] not in processes:
                continue
            K_A = self._v(r, "tool_investment_keur") * 1e3
            t0 = self._v(r, "cycle_time_s") / 3600.0                     # h
            K_CP = self._v(r, "operating_cost_eur_h")                     # EUR/h while running
            K_D = self._v(r, "personnel") * self.wage_eur_h               # EUR/h wages
            y = self._v(r, "yield_pct"); q_Q = 1.0 - (y / 100.0 if y else 0.99)
            k = (K_A / N + K_CP * t0 / (1 - q_Q) + 0.5 * K_CP * t0 * self.q_s / ((1 - q_Q) * (1 - self.q_s))
                 + K_D * t0 / ((1 - q_Q) * (1 - self.q_s)))
            out[r["process"]] = k
        out["total"] = sum(out.values())
        return out

    def active_part_usd(self) -> float:
        return self.per_unit(ACTIVE_PART)["total"] * self.eur_to_usd

    def full_motor_usd(self) -> float:
        return self.per_unit()["total"] * self.eur_to_usd
