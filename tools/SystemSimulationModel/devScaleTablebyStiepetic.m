function [ScaledMachineData,ScaledSatuMapTable] = devScaleTablebyStiepetic(scalingFactorStruct,SatuMapTable,MachineData)
    k_Axial   =scalingFactorStruct.k_Axial   ;
    k_Radial  =scalingFactorStruct.k_Radial  ;
    k_Winding =scalingFactorStruct.k_Winding ;    
    % 테이블 변수 이름 목록 가져오기
    variableNames = SatuMapTable.Properties.VariableNames;    
    ScaledSatuMapTable =SatuMapTable;
    %% 형상  K_Winding 정의하는거 추가 (n_c_ref있는지 확인해서)    
    l_stk_ref = MachineData.Stator_Lam_Length; % l_stk,ref의 값
    D_out_ref = MachineData.Stator_Lam_Dia; % D_out,ref의 값
    n_c_ref  =  MachineData.MagTurnsConductor; % turn per Coil
    a_p_ref  =  MachineData.ParallelPaths; % Parallel Path  

    ScaledMachineData.Stator_Lam_Length        = k_Axial * l_stk_ref;
    ScaledMachineData.Stator_Lam_Dia           = k_Radial * D_out_ref;    

    % Thermal Housing    
    ScaledMachineData.Rotor_Lam_Length       =ScaledMachineData.Stator_Lam_Length ;
    ScaledMachineData.Stator_Lam_Length      =ScaledMachineData.Stator_Lam_Length ;
    ScaledMachineData.Magnet_Length          =ScaledMachineData.Stator_Lam_Length ;
    
    NonActivePartLength                      = MachineData.Motor_Length -l_stk_ref;
    ScaledMachineData.Motor_Length           =ScaledMachineData.Stator_Lam_Length+NonActivePartLength;
    NonActivePartDia                         = MachineData.Housing_Dia  - MachineData.Stator_Lam_Dia;
    ScaledMachineData.Housing_Dia            =ScaledMachineData.Stator_Lam_Dia   +NonActivePartDia;

   %% Winding
    ScaledMachineData.n_c_per_ap               = k_Winding * (n_c_ref / a_p_ref);    
    ScaledMachineData.MagTurnsConductor        = scalingFactorStruct.n_c;
    ScaledMachineData.ParallelPaths            = scalingFactorStruct.a_p;

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
    ScaledSatuMapTable.CurrentDensityRMS            = 1./k_Winding*SatuMapTable.CurrentDensityRMS;
    %% [Vs]
    Psi_ew_ref =0;
    Flux_Linkage = variableNames(contains(variableNames, 'Flux_Linkage'));
    for i = 1:length(Flux_Linkage)
        ScaledSatuMapTable.(Flux_Linkage{i}) = k_Winding * k_Radial *(k_Axial*SatuMapTable.(Flux_Linkage{i}) + k_Radial * Psi_ew_ref);
    end    
    % Scaled.Flux_Linkage_D            = k_Winding * k_Radial * (k_Axial * Scaled.Flux_Linkage_D + k_Radial * Psi_ew_ref);
    % Scaled.Flux_Linkage_Q            = k_Winding * k_Radial * (k_Axial * Scaled.Flux_Linkage_Q + k_Radial * Psi_ew_ref); 
    %% Copper Loss  
    % Resistance_MotorLAB
    % EndWindingResistance_Lab
    % EndWindingInductance_Lab
    P_Cuco_ref              =3.*R_Cuco_ref.* (ScaledSatuMapTable.Stator_Current_Phase_RMS).^2;
    P_Cuew_ref              =3.*R_Cuco_ref.* (ScaledSatuMapTable.Stator_Current_Phase_RMS).^2;
   % SatuMapTable.Stator_Copper_Loss_AC             =k_Radial^2 * k_Axial*  SatuMapTable.Stator_Copper_Loss_AC   ;   
   ACConductorLossProportion_Lab=convertCharTypeData2ArrayData(MachineData.ACConductorLossProportion_Lab);
   Stator_Copper_Loss_AC=generateCuboidalACLossVariables(SatuMapTable.Stator_Copper_Loss_AC,ACConductorLossProportion_Lab);
   ScaledSatuMapTable =horzcat (ScaledSatuMapTable,Stator_Copper_Loss_AC);
   
   ScaledSatuMapTable.Stator_Copper_Loss_DC             = k_Axial * P_Cuco_ref + k_Radial * P_Cuew_ref;
    %% Mechanical 하게 처리되는 Loss들   
    ScaledSatuMapTable.Magnet_Loss                       =k_Radial^2 * k_Axial*  SatuMapTable.Magnet_Loss             ;                
    ScaledSatuMapTable.Sleeve_Loss                       =k_Radial^2 * k_Axial*  SatuMapTable.Sleeve_Loss             ;                
    ScaledSatuMapTable.Banding_Loss                      =k_Radial^2 * k_Axial*  SatuMapTable.Banding_Loss            ;   
    % Iron Loss
    % "Iron_Loss"가 포함된 변수 이름 필터링
    
    ironLossVariables = variableNames(contains(variableNames, 'Iron_Loss'));
    % 각 "Iron_Loss" 변수에 대해 연산 수행
    for i = 1:length(ironLossVariables)
        ScaledSatuMapTable.(ironLossVariables{i}) = SatuMapTable.(ironLossVariables{i}) * k_Radial^2 * k_Axial;
    end
    % Torque
    ScaledSatuMapTable.Electromagnetic_Torque            =k_Radial^2 * k_Axial*  SatuMapTable.Electromagnetic_Torque  ;                        
end