function ScaledMachineData = devScaledMachine(scalingFactorStruct,MachineData)

    k_Axial   =scalingFactorStruct.k_Axial   ;
    k_Radial  =scalingFactorStruct.k_Radial  ;
    k_Winding =scalingFactorStruct.k_Winding ;    
%% 형상  K_Winding 정의하는거 추가 (n_c_ref있는지 확인해서)    

    l_stk_ref = MachineData.Stator_Lam_Length; % l_stk,ref의 값
    D_out_ref = MachineData.Stator_Lam_Dia; % D_out,ref의 값
    if MachineData.Armature_CoilStyle==0
    n_c_ref  =  MachineData.MagTurnsConductor; % turn per Coil
    elseif MachineData.Armature_CoilStyle==1
    n_c_ref  =  MachineData.WindingLayers; % turn per Coil
    end
    a_p_ref  =  MachineData.ParallelPaths; % Parallel Path  

    ScaledMachineData.NumberOfCuboids_LossModel_Lab =MachineData.NumberOfCuboids_LossModel_Lab;
    ScaledMachineData.NumberStrandsHand =MachineData.NumberStrandsHand;
    ScaledMachineData.ACConductorLossProportion_Lab=MachineData.ACConductorLossProportion_Lab;
  %% Stator
    ScaledMachineData.Stator_Lam_Length        = k_Axial * l_stk_ref;
    ScaledMachineData.Stator_Lam_Dia           = k_Radial * D_out_ref;    
    
    %% Axial
    % Thermal Housing    
    ScaledMachineData.Rotor_Lam_Length       =ScaledMachineData.Stator_Lam_Length ;
    ScaledMachineData.Stator_Lam_Length      =ScaledMachineData.Stator_Lam_Length ;
    ScaledMachineData.Magnet_Length          =ScaledMachineData.Stator_Lam_Length ;
    
    NonActivePartLength                      = MachineData.Motor_Length -l_stk_ref;
    ScaledMachineData.Motor_Length           =ScaledMachineData.Stator_Lam_Length+NonActivePartLength;
    NonActivePartDia                         = MachineData.Housing_Dia  - MachineData.Stator_Lam_Dia;
    ScaledMachineData.Housing_Dia            =ScaledMachineData.Stator_Lam_Dia   +NonActivePartDia;
    %% Detaild Geometric

    MachineData.MagnetSeparation_Array
    % ScaledMachineData.MagnetThickness_Array=MachineData.MagnetThickness_Array;
    ScaledMachineData.MagnetThickness_Array=k_Radial*MachineData.MagnetThickness_Array;

   %% Winding
    ScaledMachineData.n_c_per_ap               = k_Winding * (n_c_ref / a_p_ref);    
    if MachineData.Armature_CoilStyle==0
    ScaledMachineData.MagTurnsConductor        = scalingFactorStruct.n_c;
    elseif MachineData.Armature_CoilStyle==1
    ScaledMachineData.WindingLayers        = scalingFactorStruct.n_c;
    end
    ScaledMachineData.ParallelPaths            = scalingFactorStruct.a_p;
    %% [Geometric]Winding  
  if MachineData.Armature_CoilStyle==0
    % n_c_ref  =  MachineData.MagTurnsConductor; % turn per Coil
  elseif MachineData.Armature_CoilStyle==1
    ScaledMachineData.Copper_Width =MachineData.Copper_Width  *k_Radial ;
    ScaledMachineData.Copper_Height=MachineData.Copper_Height *k_Radial ;
  end
     %% 저항은 별도로 End 부분이랑 Active Part 분리 필요
    % R_Cuco_ref            = SatuMapData.Phase_Resistance_DC_at_20C; % R_Cuco,ref의 값
    R_Cuco_ref              = MachineData.ResistanceActivePart;
    R_Cuew_ref              = MachineData.ResistanceEndWinding;     % R_Cuew,ref의 값 
    R_Cuco_ref=scaleResistance(R_Cuco_ref,20,MachineData.ArmatureConductor_Temperature);
    R_Cuew_ref=scaleResistance(R_Cuew_ref,20,MachineData.ArmatureConductor_Temperature);
    % 20도 기준으로 변경
    ScaledMachineData.ResistanceActivePart        = (k_Winding^2 / k_Radial^2) * (k_Axial * R_Cuco_ref);
    ScaledMachineData.ResistanceEndWinding        = (k_Winding^2 / k_Radial^2) * (k_Radial* R_Cuew_ref);
    ScaledMachineData.Resistance_MotorLAB         = (k_Winding^2 / k_Radial^2) * (k_Axial * R_Cuco_ref + k_Radial * R_Cuew_ref);
    ScaledMachineData.ArmatureWindingResistancePh = (k_Winding^2 / k_Radial^2) * (k_Axial * R_Cuco_ref + k_Radial * R_Cuew_ref);
    ScaledMachineData.ArmatureConductor_Temperature= 20;

end