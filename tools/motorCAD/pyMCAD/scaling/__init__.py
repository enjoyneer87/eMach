"""
pyMCAD/scaling — Motor-CAD SL Scaling 패키지

MATLAB defScalingFactor / defMCADMachineData4Scaling /
       getMCADBuildingData / SLScaleMachine 의 Python 구현

Quick start
-----------
>>> from pyMCAD.scaling import (
...     def_scaling_factor,
...     get_mcad_machine_data,
...     get_mcad_building_data,
...     sl_scale_machine,
...     apply_scaled_data_to_mcad,
... )
>>> import ansys.motorcad.core as pymotorcad
>>> mcad = pymotorcad.MotorCAD(open_new_instance=False)
>>> geo    = get_mcad_machine_data(mcad)
>>> factor = def_scaling_factor(2, 1, 2, geo.WindingLayers, 2, geo.WindingLayers, geo.ParallelPaths)
>>> scaled = sl_scale_machine(factor, geo)
>>> apply_scaled_data_to_mcad(scaled, mcad)
"""
from .models import ScalingFactor, MotorCADGeo, ScaledMachineData
from .helpers import scale_resistance_by_temp, calc_current_density, parse_mcad_colon_str
from .def_scaling_factor import def_scaling_factor
from .get_mcad_machine_data import get_mcad_machine_data
from .get_mcad_building_data import get_mcad_building_data
from .sl_scale_machine import sl_scale_machine
from .apply_scaled_data import apply_scaled_data_to_mcad

__all__ = [
    # 데이터 클래스
    "ScalingFactor",
    "MotorCADGeo",
    "ScaledMachineData",
    # 헬퍼
    "scale_resistance_by_temp",
    "calc_current_density",
    "parse_mcad_colon_str",
    # 핵심 함수
    "def_scaling_factor",
    "get_mcad_machine_data",
    "get_mcad_building_data",
    "sl_scale_machine",
    "apply_scaled_data_to_mcad",
]
