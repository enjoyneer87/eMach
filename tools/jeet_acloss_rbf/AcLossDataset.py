from dataclasses import dataclass, field
import numpy as np
from typing import List
from .AcLossPoint import AcLossPoint

@dataclass(frozen=True)
class AcLossDataset:
    points: List[AcLossPoint]
    
    # Exposed fields computed post-init
    speeds_k: np.ndarray = field(init=False, repr=False)
    irms_arr: np.ndarray = field(init=False, repr=False)
    phase_arr: np.ndarray = field(init=False, repr=False)
    af_arr: np.ndarray = field(init=False, repr=False)
    id_arr: np.ndarray = field(init=False, repr=False)
    iq_arr: np.ndarray = field(init=False, repr=False)
    h_ac_arr: np.ndarray = field(init=False, repr=False)
    f_ac_arr: np.ndarray = field(init=False, repr=False)
    
    LS_S: float = field(init=False)
    LS_I: float = field(init=False)
    LS_P: float = field(init=False)
    LS_ID: float = field(init=False)
    LS_IQ: float = field(init=False)
    
    def __post_init__(self):
        speeds_k = np.array([p.speed_kRPM for p in self.points], dtype=float)
        irms_arr = np.array([p.current_rms for p in self.points], dtype=float)
        phase_arr = np.array([p.phase_deg for p in self.points], dtype=float)
        af_arr = np.array([p.AF for p in self.points], dtype=float)
        id_arr = np.array([p.id_A for p in self.points], dtype=float)
        iq_arr = np.array([p.iq_A for p in self.points], dtype=float)
        h_ac_arr = np.array([p.hybrid_ac_kW for p in self.points], dtype=float)
        f_ac_arr = np.array([p.fea_ac_kW for p in self.points], dtype=float)
        
        ls_s = float(speeds_k.std()) if len(speeds_k) > 1 and speeds_k.std() > 0 else 1.0
        ls_i = float(irms_arr.std()) if len(irms_arr) > 1 and irms_arr.std() > 0 else 1.0
        ls_p = float(phase_arr.std()) if len(phase_arr) > 1 and phase_arr.std() > 0 else 1.0
        ls_id = float(id_arr.std()) if len(id_arr) > 1 and id_arr.std() > 0 else 1.0
        ls_iq = float(iq_arr.std()) if len(iq_arr) > 1 and iq_arr.std() > 0 else 1.0
        
        object.__setattr__(self, 'speeds_k', speeds_k)
        object.__setattr__(self, 'irms_arr', irms_arr)
        object.__setattr__(self, 'phase_arr', phase_arr)
        object.__setattr__(self, 'af_arr', af_arr)
        object.__setattr__(self, 'id_arr', id_arr)
        object.__setattr__(self, 'iq_arr', iq_arr)
        object.__setattr__(self, 'h_ac_arr', h_ac_arr)
        object.__setattr__(self, 'f_ac_arr', f_ac_arr)
        object.__setattr__(self, 'LS_S', ls_s)
        object.__setattr__(self, 'LS_I', ls_i)
        object.__setattr__(self, 'LS_P', ls_p)
        object.__setattr__(self, 'LS_ID', ls_id)
        object.__setattr__(self, 'LS_IQ', ls_iq)
        
    def __len__(self) -> int:
        return len(self.points)
