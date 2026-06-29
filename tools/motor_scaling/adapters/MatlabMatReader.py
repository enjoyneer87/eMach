import numpy as np
from scipy.io import loadmat
from ..model.BaseMotorMap import BaseMotorMap

class MatlabMatReader:
    @staticmethod
    def read(filepath: str, r_dc: float = 0.05, pole_pairs: int = 4) -> BaseMotorMap:
        """
        Reads motor flux and loss grids from a MATLAB .mat file.
        Supports variables like:
            - Id, Iq: grid arrays or vectors
            - Fd, Fq: d/q-axis flux linkages [Vs]
            - Rs: stator resistance [Ohm] (used if present, else uses default)
            - P_fe / Loss / IronLoss: 2D iron loss grid
            - P_cu_ac / ACLoss: 2D AC copper loss grid
        """
        data = loadmat(filepath)
        
        # Helper to extract a clean numpy array
        def get_arr(key, default=None):
            if key in data:
                val = data[key]
                # Squeeze to remove single-dimensional axes
                return np.squeeze(val)
            return default
            
        # Try to find Id and Iq
        id_val = get_arr('Id')
        iq_val = get_arr('Iq')
        
        # If they are 1D vectors, convert to 2D meshgrid
        if id_val is not None and iq_val is not None:
            if id_val.ndim == 1 and iq_val.ndim == 1:
                id_grid, iq_grid = np.meshgrid(id_val, iq_val)
            else:
                id_grid, iq_grid = id_val, iq_val
        else:
            raise ValueError("MAT file must contain 'Id' and 'Iq' variables.")
            
        # Try to find flux linkages Fd and Fq (or lambda_d/q)
        lambda_d = get_arr('Fd') or get_arr('lambda_d') or get_arr('FluxLinkageD')
        lambda_q = get_arr('Fq') or get_arr('lambda_q') or get_arr('FluxLinkageQ')
        
        if lambda_d is None or lambda_q is None:
            raise ValueError("MAT file must contain flux linkage variables ('Fd'/'Fq' or 'lambda_d'/'lambda_q').")
            
        # Try to find stator resistance
        rs = get_arr('Rs') or get_arr('r_dc')
        if rs is not None:
            r_dc = float(rs)
            
        # Try to find pole pairs
        p_pairs = get_arr('p') or get_arr('pole_pairs')
        if p_pairs is not None:
            pole_pairs = int(p_pairs)
            
        # Try to find losses (Iron loss and AC copper loss)
        p_fe = get_arr('Pfe') or get_arr('IronLoss') or get_arr('p_fe_grid')
        if p_fe is None:
            p_fe = np.zeros_like(lambda_d) # fallback if missing
            
        p_ac = get_arr('Pac') or get_arr('ACLoss') or get_arr('hybrid_Total_kW') or get_arr('p_cu_ac_hybrid')
        if p_ac is None:
            p_ac = np.zeros_like(lambda_d) # fallback if missing
            
        return BaseMotorMap(
            id_grid=id_grid,
            iq_grid=iq_grid,
            lambda_d=lambda_d,
            lambda_q=lambda_q,
            r_dc=r_dc,
            p_fe_grid=p_fe,
            p_cu_ac_hybrid=p_ac,
            pole_pairs=pole_pairs
        )
