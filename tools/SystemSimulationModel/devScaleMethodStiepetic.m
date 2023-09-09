function Scaled = devScaleMethodStiepetic(scalingFactorStruct,SatuMapData,MachineData)
    k_Axial   =scalingFactorStruct.k_Axial   ;
    k_Radial  =scalingFactorStruct.k_Radial  ;
    k_Winding =scalingFactorStruct.k_Winding ;
    
    %% K_Winding 정의하는거 추가 (n_c_ref있는지 확인해서)
    
    l_stk_ref = MachineData.ll; % l_stk,ref의 값
    D_out_ref = MachineData.D_out; % D_out,ref의 값
    n_c_ref = MachineData.turnperCoil; % turn per Coil
    a_p_ref = MachineData.ParallelPath; % Parallel Path
    
    % % 레퍼런스 값들
    Psi_dco_ref             = SatuMapData.Flux_Linkage_D; % Psi_dco,ref의 값
    Psi_ew_ref              = 0 % Psi_ew,ref의 값;
    Psi_qco_ref             = SatuMapData.Flux_Linkage_Q; % Psi_qco,ref의 값
    
    %% Copper Loss 
    R_Cuco_ref              = SatuMapData.Phase_Resistance_DC_at_20C; % R_Cuco,ref의 값
    R_Cuew_ref              = 0; % R_Cuew,ref의 값
    P_Cuco_ref              = SatuMapData.Stator_Copper_Loss_DC; % P_Cuco,ref의 값
    P_Cuew_ref              = 0 % P_Cuew,ref의 값
    
    %%
    P_Fe_ref                = SatuMapData.Iron_Loss;% P_Fe,ref의 값
    P_PM_ref                = SatuMapData.Magnet_Loss; % P_PM,ref의 값
    P_mech_ref              = SatuMapData.Stator_Copper_Loss_AC; % P_mech,ref의 값
    
    % Torque
    Electromagnetic_Torque                = SatuMapData.Electromagnetic_Torque;              % T_sh,ref의 값
    
    %%
    
    Scaled=struct()
    
    % 계산
    Scaled.l_stk            = k_Axial * l_stk_ref;
    Scaled.D_out            = k_Radial * D_out_ref;
    
    Scaled.n_c_per_ap       = k_Winding * (n_c_ref / a_p_ref);
    
    
    %
    Scaled.CurrentDensity = 1./k_Winding*SatuMapData.CurrentDensityRMS;
    Scaled.Stator_Current_Line_Peak  = 1./k_Winding.*k_Radial.*SatuMapData.Stator_Current_Line_Peak; 
    
    Scaled.Id_Peak  = 1./k_Winding.*k_Radial.*SatuMapData.Id_Peak ;
    Scaled.Iq_Peak  = 1./k_Winding.*k_Radial.*SatuMapData.Iq_Peak ;
    
    % 계산
    Scaled.Flux_Linkage_D            = k_Winding * k_Radial * (k_Axial * Psi_dco_ref + k_Radial * Psi_ew_ref);
    Scaled.Flux_Linkage_Q            = k_Winding * k_Radial * (k_Axial * Psi_qco_ref + k_Radial * Psi_ew_ref);
    
    %
    Scaled.R_ph              = (k_Winding^2 / k_Radial^2) * (k_Axial * R_Cuco_ref + k_Radial * R_Cuew_ref);
    Scaled.P_Cu              = k_Axial * P_Cuco_ref + k_Radial * P_Cuew_ref;
    
    %%
    Scaled.P_Fe             = k_Radial^2 * k_Axial * P_Fe_ref;
    Scaled.P_PM             = k_Radial^2 * k_Axial * P_PM_ref;
    Scaled.P_mech           = k_Radial^2 * k_Axial * P_mech_ref;
    Scaled.Electromagnetic_Torque             = k_Radial^2 * k_Axial * Electromagnetic_Torque;
end