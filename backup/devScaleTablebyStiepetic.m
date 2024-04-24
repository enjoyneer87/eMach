function [ScaledMachineData,ScaledSatuMapTable] = devScaleTablebyStiepetic(scalingFactorStruct,SatuMapTable,BuildingData)
    k_Axial   =scalingFactorStruct.k_Axial   ;
    k_Radial  =scalingFactorStruct.k_Radial  ;
    k_Winding =scalingFactorStruct.k_Winding ;    
    scalingFactorStruct.n_c =scalingFactorStruct.turns_per_coil;
    
    MotorCADGeo =BuildingData.MotorCADGeo;

% ArmatureConductor_Temperature - Emag -% TwindingCalc_MotorLAB 와 동일
% Twdg_MotorLAB                 - Lab (만들어질때 Emag기준)

    % 테이블 변수 이름 목록 가져오기
    variableNames = SatuMapTable.Properties.VariableNames;    
    ScaledSatuMapTable =SatuMapTable;
    %% 형상  K_Winding 정의하는거 추가 (n_c_ref있는지 확인해서)    
    l_stk_ref = MotorCADGeo.Stator_Lam_Length; % l_stk,ref의 값
    D_out_ref = MotorCADGeo.Stator_Lam_Dia; % D_out,ref의 값
    if MotorCADGeo.Armature_CoilStyle==0
        n_c_ref  =  MotorCADGeo.MagTurnsConductor; % turn per Coil
    elseif MotorCADGeo.Armature_CoilStyle==1
        n_c_ref  =  MotorCADGeo.WindingLayers; % turn per Coil
    end

    a_p_ref  =  MotorCADGeo.ParallelPaths; % Parallel Path  
    ScaledMachineData.refMachineData                                 =MotorCADGeo;
    ScaledMachineData.refBuildingData                                =BuildingData;
    ScaledMachineData.refSatuMapTable                                =SatuMapTable;
    ScaledMachineData.scalingFactor                                  =scalingFactorStruct;
    ScaledMachineData.NumberOfCuboids_LossModel_Lab                  =MotorCADGeo.NumberOfCuboids_LossModel_Lab;
    ScaledMachineData.NumberStrandsHand                              =MotorCADGeo.NumberStrandsHand;
    ScaledMachineData.ACConductorLossProportion_Lab                  =MotorCADGeo.ACConductorLossProportion_Lab;

    %% Stator
    ScaledMachineData.Stator_Lam_Length        = k_Axial * l_stk_ref;
    ScaledMachineData.Stator_Lam_Dia           = k_Radial * D_out_ref;    
    
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
    ScaledMachineData.MagnetThickness_Array=k_Radial*MotorCADGeo.MagnetThickness_Array;


 

   %% Winding
    ScaledMachineData.n_c_per_ap               = k_Winding * (n_c_ref / a_p_ref);    
    if MotorCADGeo.Armature_CoilStyle==0
    ScaledMachineData.MagTurnsConductor        = scalingFactorStruct.n_c;
    elseif MotorCADGeo.Armature_CoilStyle==1
    ScaledMachineData.WindingLayers        = scalingFactorStruct.n_c;
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
    % R_Cuco_ref            = SatuMapData.Phase_Resistance_DC_at_20C; % R_Cuco,ref의 값
    R_Cuco_ref              = MotorCADGeo.ResistanceActivePart;
    R_Cuew_ref              = MotorCADGeo.EndWindingResistance_Lab;     % R_Cuew,ref의 값 

    %% Export Tool에서 
    % 무조건 20도로 변환
    ScaledMachineData.Twdg_MotorLAB                 = 20;
    ScaledMachineData.ArmatureConductor_Temperature = 20;
    ScaledMachineData.TwindingCalc_MotorLAB         = 20;

    R_Cuco_ref20=scaleResistancebyTemp(R_Cuco_ref,20,BuildingData.Twdg_MotorLAB);
    R_Cuew_ref20=scaleResistancebyTemp(R_Cuew_ref,20,BuildingData.Twdg_MotorLAB);
   % testR=scaleResistancebyTemp(    0.004285,65,20);
    ScaledMachineData.ResistanceActivePart20        = (k_Winding^2 / k_Radial^2) * (k_Axial * R_Cuco_ref20);
    ScaledMachineData.EndWindingResistance_Lab20    = (k_Winding^2 / k_Radial^2) * (k_Radial* R_Cuew_ref20);
    ScaledMachineData.Resistance_MotorLAB20         = (k_Winding^2 / k_Radial^2) * (k_Axial * R_Cuco_ref20 + k_Radial * R_Cuew_ref20);
    ScaledMachineData.ArmatureWindingResistancePh20 = (k_Winding^2 / k_Radial^2) * (k_Axial * R_Cuco_ref20 + k_Radial * R_Cuew_ref20);
    
    ScaledMachineData.ResistanceActivePart              =ScaledMachineData.ResistanceActivePart20            ;
    ScaledMachineData.EndWindingResistance_Lab          =ScaledMachineData.EndWindingResistance_Lab20     ;
    ScaledMachineData.Resistance_MotorLAB               =ScaledMachineData.Resistance_MotorLAB20          ;
    ScaledMachineData.ArmatureWindingResistancePh       =ScaledMachineData.ArmatureWindingResistancePh20 ;     %% Inductance
    ScaledMachineData.EndWindingInductance_Lab          =k_Radial*MotorCADGeo.EndWindingInductance_Lab;
    
    %% unit으로 분리해야할듯 
    
    % Ampere [A]
    CurrentVariables = variableNames(contains(variableNames, 'Current'));
    % 각 "Current" 변수에 대해 연산 수행
    for i = 1:length(CurrentVariables)
        ScaledSatuMapTable.(CurrentVariables{i}) = 1./k_Winding.*k_Radial.*SatuMapTable.(CurrentVariables{i});
    end
    ScaledSatuMapTable.Id_Peak                   = 1./k_Winding.*k_Radial.*SatuMapTable.Id_Peak ;
    ScaledSatuMapTable.Iq_Peak                   = 1./k_Winding.*k_Radial.*SatuMapTable.Iq_Peak ;
    % Ampere/m2
    SatuMapTable.CurrentDensityRMS               =calcCurrentDensity(SatuMapTable.Stator_Current_Line_RMS,MotorCADGeo.ParallelPaths,double(MotorCADGeo.NumberStrandsHand),MotorCADGeo.ArmatureConductorCSA);
    ScaledSatuMapTable.CurrentDensityRMS         = 1./k_Winding*SatuMapTable.CurrentDensityRMS;

    ScaledMachineData.Ipk                        =max(ScaledSatuMapTable.Stator_Current_Phase_Peak);
    ScaledMachineData.Irms                       =max(ScaledSatuMapTable.Stator_Current_Phase_RMS);

    %% [Vs]
    Psi_ew_ref                                   =0;
    Flux_Linkage                                 = variableNames(contains(variableNames, 'Flux_Linkage'));
    for i = 1:length(Flux_Linkage)
        ScaledSatuMapTable.(Flux_Linkage{i})     = k_Winding * k_Radial *(k_Axial*SatuMapTable.(Flux_Linkage{i}) + k_Radial * Psi_ew_ref);
    end    
    % Scaled.Flux_Linkage_D            = k_Winding * k_Radial * (k_Axial * Scaled.Flux_Linkage_D + k_Radial * Psi_ew_ref);
    % Scaled.Flux_Linkage_Q            = k_Winding * k_Radial * (k_Axial * Scaled.Flux_Linkage_Q + k_Radial * Psi_ew_ref); 
   %% Copper Loss  
    % Resistance_MotorLAB
    % EndWindingResistance_Lab
    % EndWindingInductance_Lab
    P_Cuco_ref20                                 =3.*R_Cuco_ref20.* (SatuMapTable.Stator_Current_Phase_RMS).^2;
    P_Cuew_ref20                                 =3.*R_Cuew_ref20.* (SatuMapTable.Stator_Current_Phase_RMS).^2;
    % ScaledSatuMapTable.Stator_Copper_Loss_DC             = k_Axial * P_Cuco_ref20 + k_Radial * P_Cuew_ref20;
    R_Cuco20                                     =ScaledMachineData.ResistanceActivePart20    ;
    R_Cuew20                                     =ScaledMachineData.EndWindingResistance_Lab20;
    R_Cu20                                       =ScaledMachineData.Resistance_MotorLAB20  ;   
    ScaledSatuMapTable.Stator_Copper_Loss_DC     =3*(R_Cuco20+R_Cuew20)*(ScaledSatuMapTable.Stator_Current_Phase_RMS).^2;
    ScaledSatuMapTable.Stator_Copper_Loss_DC20   =ScaledSatuMapTable.Stator_Copper_Loss_DC;
  %% [WIP] AC Los Scaling
   ScaledMachineData.HybridAdjustmentFactor_ACLosses  =1;
   ScaledMachineData.WindingTemp_ACLoss_Ref_Lab       =BuildingData.TwindingCalc_MotorLAB;
   % tempScalingFactor=createTempScalingFactor(BuildingData.TwindingCalc_MotorLAB,BuildingData.WindingTemp_ACLoss_Ref_Lab,0.00393);
   tempScalingFactor=1;
   ScaledSatuMapTable.Stator_Copper_Loss_AC           =k_Radial^4 * k_Axial*  SatuMapTable.Stator_Copper_Loss_AC*tempScalingFactor;   
   % ACConductorLossProportion_Lab=convertCharTypeData2ArrayData(MotorCADGeo.ACConductorLossProportion_Lab);
   % Stator_Copper_Loss_AC=generateCuboidalACLossVariables(SatuMapTable.Stator_Copper_Loss_AC,ACConductorLossProportion_Lab);
   % ScaledSatuMapTable =horzcat (ScaledSatuMapTable,Stator_Copper_Loss_AC);
 
   ScaledSatuMapTable.Stator_Copper_Loss              =ScaledSatuMapTable.Stator_Copper_Loss_DC +ScaledSatuMapTable.Stator_Copper_Loss_AC; 
   %% Mechanical 하게 처리되는 Loss들   
    ScaledSatuMapTable.Magnet_Loss                    =k_Radial^2 * k_Axial*  SatuMapTable.Magnet_Loss             ;                
    ScaledSatuMapTable.Sleeve_Loss                    =k_Radial^2 * k_Axial*  SatuMapTable.Sleeve_Loss             ;                
    ScaledSatuMapTable.Banding_Loss                   =k_Radial^2 * k_Axial*  SatuMapTable.Banding_Loss            ;   
    % Iron Loss
    % "Iron_Loss"가 포함된 변수 이름 필터링
    
    ironLossVariables = variableNames(contains(variableNames, 'Iron_Loss'));
    % 각 "Iron_Loss" 변수에 대해 연산 수행
    for i = 1:length(ironLossVariables)
        ScaledSatuMapTable.(ironLossVariables{i}) = SatuMapTable.(ironLossVariables{i}) * k_Radial^2 * k_Axial;
    end
    % Torque
    ScaledSatuMapTable.Electromagnetic_Torque            =k_Radial^2 * k_Axial*  SatuMapTable.Electromagnetic_Torque  ;                        
    %% Total Loss
    ScaledSatuMapTable.Total_Loss= ScaledSatuMapTable.Magnet_Loss +ScaledSatuMapTable.Banding_Loss+ScaledSatuMapTable.Stator_Copper_Loss+ScaledSatuMapTable.Iron_Loss;
end