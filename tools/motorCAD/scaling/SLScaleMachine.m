

function ScaledMachineData = SLScaleMachine(scalingFactorStruct,MotorCADGeo,BuildingData)
    % MotorCADGeo =refLABBuildData.MotorCADGeo;

    if nargin==3
    ScaledMachineData.refBuildingData=BuildingData;
    end
    k_Axial   =scalingFactorStruct.k_Axial   ;
    k_Radial  =scalingFactorStruct.k_Radial  ;
    k_Winding =scalingFactorStruct.k_Winding ;    

    if isfield(scalingFactorStruct,'turns_per_coil')
    scalingFactorStruct.n_c                 =scalingFactorStruct.turns_per_coil;    
    end
    % ArmatureConductor_Temperature - Emag -% TwindingCalc_MotorLAB 와 동일
    % Twdg_MotorLAB                 - Lab (만들어질때 Emag기준)
    % LabTable=originTable;
%% 형상 K_Winding 정의하는거 추가 (n_c_ref있는지 확인해서)

    l_stk_ref = MotorCADGeo.Stator_Lam_Length; % l_stk,ref의 값
    D_out_ref = MotorCADGeo.Stator_Lam_Dia; % D_out,ref의 값

    if MotorCADGeo.Armature_CoilStyle==0
    n_c_ref  =  MotorCADGeo.MagTurnsConductor; % turn per Coil
    elseif MotorCADGeo.Armature_CoilStyle==1
    n_c_ref  =  MotorCADGeo.WindingLayers; % turn per Coil
    end
    a_p_ref  =  MotorCADGeo.ParallelPaths; % Parallel Path  

    %%
    ScaledMachineData.NumberOfCuboids_LossModel_Lab =MotorCADGeo.NumberOfCuboids_LossModel_Lab;
    ScaledMachineData.NumberStrandsHand =MotorCADGeo.NumberStrandsHand;
    ScaledMachineData.ACConductorLossProportion_Lab=MotorCADGeo.ACConductorLossProportion_Lab;

%  Insulation

    ScaledMachineData.Insulation_Thickness =k_Radial*MotorCADGeo.Insulation_Thickness ;
    ScaledMachineData.Liner_Thickness      =k_Radial*MotorCADGeo.Liner_Thickness      ;
    ScaledMachineData.ConductorSeparation  =k_Radial*MotorCADGeo.ConductorSeparation  ;


%% Stator

    ScaledMachineData.Stator_Lam_Length        = k_Axial * l_stk_ref;
    ScaledMachineData.Stator_Lam_Dia           = k_Radial * D_out_ref;
    ScaledMachineData.Tooth_Tip_Depth          =k_Radial*MotorCADGeo.Tooth_Tip_Depth;
    ScaledMachineData.MinBackIronThickness     =k_Radial*MotorCADGeo.MinBackIronThickness;
%% Axial
% Thermal Housing 

    ScaledMachineData.Rotor_Lam_Length       =ScaledMachineData.Stator_Lam_Length ;
    ScaledMachineData.Stator_Lam_Length      =ScaledMachineData.Stator_Lam_Length ;
    ScaledMachineData.Magnet_Length          =ScaledMachineData.Stator_Lam_Length ;
   
    NonActivePartLength                      = MotorCADGeo.Motor_Length -l_stk_ref;
    ScaledMachineData.Motor_Length           =ScaledMachineData.Stator_Lam_Length+NonActivePartLength;
    NonActivePartDia                         = MotorCADGeo.Housing_Dia  - MotorCADGeo.Stator_Lam_Dia;
    ScaledMachineData.Housing_Dia            =ScaledMachineData.Stator_Lam_Dia   +NonActivePartDia;
%% Detaild Geometric

    MotorCADGeo.MagnetSeparation_Array;
    % ScaledMachineData.MagnetThickness_Array=MachineData.MagnetThickness_Array;
    ScaledMachineData.MagnetSeparation_Array=k_Radial*MotorCADGeo.MagnetSeparation_Array;
    ScaledMachineData.MagnetThickness_Array =k_Radial*MotorCADGeo.MagnetThickness_Array;
%% [TB]Winding
% n_c  turn per Coil
% n_c_per_ap % turn per Coil per ParallelPaths
    ScaledMachineData.n_c_per_ap               = k_Winding * (n_c_ref / a_p_ref);   %  

    if MotorCADGeo.Armature_CoilStyle==0
    ScaledMachineData.MagTurnsConductor        = scalingFactorStruct.n_c;

    elseif MotorCADGeo.Armature_CoilStyle==1
    ScaledMachineData.WindingLayers            = scalingFactorStruct.n_c;
    end
    ScaledMachineData.ParallelPaths            = scalingFactorStruct.a_p;

%% [Geometric]Winding

  if MotorCADGeo.Armature_CoilStyle==0
    % n_c_ref  =  MachineData.MagTurnsConductor; % turn per Coil
  elseif MotorCADGeo.Armature_CoilStyle==1
    ScaledMachineData.Copper_Width =MotorCADGeo.Copper_Width  *k_Radial ;
    ScaledMachineData.Copper_Height=MotorCADGeo.Copper_Height *k_Radial ;
  end
%% 저항은 별도로 End 부분이랑 Active Part 분리 필요
% R_Cuco_ref = SatuMapData.Phase_Resistance_DC_at_20C; % R_Cuco,ref의 값

    R_Cuco_ref              = MotorCADGeo.ResistanceActivePart;
    R_Cuew_ref              = MotorCADGeo.EndWindingResistance_Lab;     % R_Cuew,ref의 값
    % 4 retro
    MotorCADGeo.R_Cuco_ref  = R_Cuco_ref;
    MotorCADGeo.R_Cuew_ref  = R_Cuew_ref;
%% If LabTable

    ScaledMachineData.Twdg_MotorLAB                 = MotorCADGeo.Twdg_MotorLAB;
    ScaledMachineData.ArmatureConductor_Temperature = MotorCADGeo.ArmatureConductor_Temperature;
    ScaledMachineData.TwindingCalc_MotorLAB         = MotorCADGeo.Twdg_MotorLAB;
    % Building Data Needed
    % MotorCADGeo=tempDefMCADMachineData4Scaling(mcad(1))
    % MotorCADGeo.ArmatureConductor_Temperature
    % MotorCADGeo.Twdg_MotorLAB
    % TwindingCalc_MotorLAB
    R_Cuco_ref20=scaleResistancebyTemp(R_Cuco_ref,20,MotorCADGeo.ArmatureConductor_Temperature);
    R_Cuew_ref20=scaleResistancebyTemp(R_Cuew_ref,20,MotorCADGeo.ArmatureConductor_Temperature);
%% 
%% 
% 0.00993


    % 4 retro
    MotorCADGeo.R_Cuco_ref20=R_Cuco_ref20;
    MotorCADGeo.R_Cuew_ref20=R_Cuew_ref20;
    ScaledMachineData.refMachineData=MotorCADGeo;

    ScaledMachineData.scalingFactor =scalingFactorStruct;
    % 20도 기준으로 변경
    ScaledMachineData.ResistanceActivePart20        = (k_Winding^2 / k_Radial^2) * (k_Axial * R_Cuco_ref20);
    ScaledMachineData.EndWindingResistance_Lab20    = (k_Winding^2 / k_Radial^2) * (k_Radial* R_Cuew_ref20);
    ScaledMachineData.Resistance_MotorLAB20         = (k_Winding^2 / k_Radial^2) * (k_Axial * R_Cuco_ref20 + k_Radial * R_Cuew_ref20);
    ScaledMachineData.ArmatureWindingResistancePh20 = (k_Winding^2 / k_Radial^2) * (k_Axial * R_Cuco_ref20 + k_Radial * R_Cuew_ref20);

    %% ArmatureConductor_Temperature 기준으로 변경
    ScaledMachineData.ResistanceActivePart                =scaleResistancebyTemp(ScaledMachineData.ResistanceActivePart20 ,MotorCADGeo.ArmatureConductor_Temperature,20)           ;
    ScaledMachineData.EndWindingResistance_Lab            =scaleResistancebyTemp(ScaledMachineData.EndWindingResistance_Lab20,MotorCADGeo.ArmatureConductor_Temperature,20)        ;
    ScaledMachineData.Resistance_MotorLAB                 =scaleResistancebyTemp(ScaledMachineData.Resistance_MotorLAB20,MotorCADGeo.ArmatureConductor_Temperature,20)               ;
    ScaledMachineData.ArmatureWindingResistancePh         =scaleResistancebyTemp(ScaledMachineData.ArmatureWindingResistancePh20,MotorCADGeo.ArmatureConductor_Temperature,20)  ;     

    %% EndInductance
    ScaledMachineData.EndWindingInductance_Lab            = k_Radial*MotorCADGeo.EndWindingInductance_Lab;

end