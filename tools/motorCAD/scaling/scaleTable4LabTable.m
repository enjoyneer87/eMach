function [ScaledMachineData,SLLawScaledLabTable,refLabTable]                 = scaleTable4LabTable(scalingFactorStruct,refLabTable,BuildingData,LabTableType)
%  SCALETABLE4LABTABLE 
   
   %% BuildingData                =BuildData
   % BuildingData                =refLABBuildData
   % scalingFactorStruct                =Factor
    k_Axial                   =scalingFactorStruct.k_Axial   ;
    k_Radial                  =scalingFactorStruct.k_Radial  ;
    k_Winding                 =scalingFactorStruct.k_Winding ;    
    if isfield(scalingFactorStruct,'turns_per_coil')
    scalingFactorStruct.n_c                 =scalingFactorStruct.turns_per_coil;    
    end
    MotorCADGeo                 =BuildingData.MotorCADGeo;
    % ArmatureConductor_Temperature - Emag -% TwindingCalc_MotorLAB 와 동일
    % Twdg_MotorLAB                 - Lab (만들어질때 Emag기준)
    % LabTable                =originTable;
    % 테이블 변수 이름 목록 가져오기
    variableNames                       = refLabTable.Properties.VariableNames;    
    SLLawScaledLabTable                 =refLabTable;
%% ScaledMachineData - SLScaleMachine
    ScaledMachineData                 = SLScaleMachine(scalingFactorStruct,MotorCADGeo);
%% If Export Tool Data 에서
% 무조건 20도로 변환
if nargin                ==4&&strcmp(LabTableType,'SatuMapExportTool')
    ScaledMachineData.Twdg_MotorLAB                                 = 20;
    ScaledMachineData.ArmatureConductor_Temperature                 = 20;
    ScaledMachineData.TwindingCalc_MotorLAB                         = 20;
    %% ArmatureConductor_Temperature 기준으로 변경
    ScaledMachineData.ResistanceActivePart                                =ScaledMachineData.ResistanceActivePart20;
    ScaledMachineData.EndWindingResistance_Lab                            =ScaledMachineData.EndWindingResistance_Lab20     ;
    ScaledMachineData.Resistance_MotorLAB                                 =ScaledMachineData.Resistance_MotorLAB20          ;
    ScaledMachineData.ArmatureWindingResistancePh                         =ScaledMachineData.ArmatureWindingResistancePh20 ;    
end    
%% [WIP]unit으로 분리해야할듯
    % Ampere [A]
    CurrentVariables                 = variableNames(contains(variableNames, 'Is'));
    if isvarofTable(refLabTable,'Is')                ==0
    CurrentVariables                 = variableNames(contains(variableNames, 'Current'));
    CurrentVariables                =strrep(CurrentVariables,'Current Angle','');
    end
   %% 
% Current 정의
    if isvarofTable(refLabTable,'Is')
        Is                =refLabTable.Is;
        ScaledIsPk                =SLLawScaledLabTable.Is;
        disp('Direct Export')
    end
    
    if isvarofTable(refLabTable,'Stator_Current_Phase_Peak')
    Is                =refLabTable.Stator_Current_Phase_Peak;
    ScaledIsPk                =SLLawScaledLabTable.Stator_Current_Phase_Peak;
    end
    
    %%
    % 각 "Current" 변수에 대해 연산 수행
    for i                 = 1:length(CurrentVariables)
        SLLawScaledLabTable.(CurrentVariables{i})                 = 1./k_Winding.*k_Radial.*refLabTable.(CurrentVariables{i});
    end
    % ScaledSatuMapTable.Id_Peak                                   = 1./k_Winding.*k_Radial.*LabTable.Id_Peak ;
    % ScaledSatuMapTable.Iq_Peak                                   = 1./k_Winding.*k_Radial.*LabTable.Iq_Peak ;
    % Ampere/m2
    % LabTable.CurrentDensityRMS                =calcCurrentDensity((LabTable.Is)/sqrt(2),MotorCADGeo.ParallelPaths,double(MotorCADGeo.NumberStrandsHand),MotorCADGeo.ArmatureConductorCSA);
    refLabTable.CurrentDensityRMS                =calcCurrentDensity((Is)/sqrt(2),MotorCADGeo.ParallelPaths,double(MotorCADGeo.NumberStrandsHand),MotorCADGeo.ArmatureConductorCSA);
    SLLawScaledLabTable.CurrentDensityRMS                            = 1./k_Winding*refLabTable.CurrentDensityRMS;
    ScaledMachineData.Ipk                =max(ScaledIsPk);
    ScaledMachineData.Irms                =max(ScaledIsPk)/sqrt(2);
%% [Vs]
    Psi_ew_ref                 =0;
    Flux_Linkage                 = variableNames(contains(variableNames, 'Flux Linkage'));
    for i                 = 1:length(Flux_Linkage)
        SLLawScaledLabTable.(Flux_Linkage{i})                 = k_Winding * k_Radial *(k_Axial*refLabTable.(Flux_Linkage{i}) + k_Radial * Psi_ew_ref);
    end    
    % Scaled.Flux_Linkage_D                            = k_Winding * k_Radial * (k_Axial * Scaled.Flux_Linkage_D + k_Radial * Psi_ew_ref);
    % Scaled.Flux_Linkage_Q                            = k_Winding * k_Radial * (k_Axial * Scaled.Flux_Linkage_Q + k_Radial * Psi_ew_ref);
%% Copper Loss
% Resistance_MotorLAB
% 
% EndWindingResistance_Lab
% 
% EndWindingInductance_Lab
    %% RefData
    R_Cuco_ref20                 = ScaledMachineData.refMachineData.R_Cuco_ref20;
    R_Cuew_ref20                 = ScaledMachineData.refMachineData.R_Cuew_ref20;
    P_Cuco_ref20                              =3.*R_Cuco_ref20.* pk2rms(Is).^2;
    P_Cuew_ref20                              =3.*R_Cuew_ref20.* pk2rms(Is).^2;
    refLabTable.Stator_Copper_Loss_DC                          =3*(P_Cuco_ref20+P_Cuew_ref20).*pk2rms(Is).^2;
    refLabTable.Stator_Copper_Loss_DC20                =P_Cuco_ref20+P_Cuew_ref20;
    %% Scaled 
    % ScaledSatuMapTable.Stator_Copper_Loss_DC                             = k_Axial * P_Cuco_ref20 + k_Radial * P_Cuew_ref20;
    R_Cuco20                =ScaledMachineData.ResistanceActivePart20    ;
    R_Cuew20                =ScaledMachineData.EndWindingResistance_Lab20;
    R_Cu20                 =ScaledMachineData.Resistance_MotorLAB20  ;   
    SLLawScaledLabTable.Stator_Copper_Loss_DC                          =3*(R_Cuco20+R_Cuew20).*pk2rms(ScaledIsPk).^2;
    SLLawScaledLabTable.Stator_Copper_Loss_DC20                =SLLawScaledLabTable.Stator_Copper_Loss_DC;
%% AC Los Scaling
   ScaledMachineData.HybridAdjustmentFactor_ACLosses                  =1;
   ScaledMachineData.WindingTemp_ACLoss_Ref_Lab                =BuildingData.TwindingCalc_MotorLAB;
   tempScalingFactor                =createTempScalingFactor(BuildingData.TwindingCalc_MotorLAB,BuildingData.WindingTemp_ACLoss_Ref_Lab,0.00393);
   ScaledMachineData.tempScalingFactor                =tempScalingFactor;
   % tempScalingFactor                =1;
   variableNames                =refLabTable.Properties.VariableNames;
   ACLossIndex                =contains(variableNames,'AC Copper');
   ACLossVar                = variableNames(ACLossIndex);
   for i                =1:length(ACLossVar)
   ACLossVarName                =ACLossVar{i}    ;
   SLLawScaledLabTable.(ACLossVarName)                  =k_Radial^4 * k_Axial*  SLLawScaledLabTable.(ACLossVarName)/tempScalingFactor;  
   end
   % ACConductorLossProportion_Lab                =convertCharTypeData2ArrayData(MotorCADGeo.ACConductorLossProportion_Lab);
   % Stator_Copper_Loss_AC                =generateCuboidalACLossVariables(SatuMapTable.Stator_Copper_Loss_AC,ACConductorLossProportion_Lab);
   % ScaledSatuMapTable                 =horzcat (ScaledSatuMapTable,Stator_Copper_Loss_AC); 
   % ScaledSatuMapTable.Stator_Copper_Loss                =ScaledSatuMapTable.Stator_Copper_Loss_DC +ScaledSatuMapTable.Stator_Copper_Loss_AC;
   % 
%% Mechanical 하게 처리되는 Loss들
   if isvarofTable(SLLawScaledLabTable,'Magnet Loss')
   SLLawScaledLabTable.("Magnet Loss")                                   =k_Radial^4 * k_Axial*  refLabTable.("Magnet Loss")         ;                
   end
   if  isvarofTable(SLLawScaledLabTable,'Sleeve_Loss')
    SLLawScaledLabTable.Sleeve_Loss                                       =k_Radial^2 * k_Axial*  refLabTable.Sleeve_Loss             ;                
   end
   if  isvarofTable(SLLawScaledLabTable,'Banding Loss')
   SLLawScaledLabTable.("Banding Loss")                                  =k_Radial^4 * k_Axial*  refLabTable.("Banding Loss")        ;   
   end
   %% Iron Loss
    % "Iron_Loss"가 포함된 변수 이름 필터링
    
    ironLossVariables                 = variableNames(contains(variableNames, 'Iron'));
    % 각 "Iron_Loss" 변수에 대해 연산 수행
    for i                 = 1:length(ironLossVariables)
        SLLawScaledLabTable.(ironLossVariables{i})                 = refLabTable.(ironLossVariables{i}) * k_Radial^2 * k_Axial;
    end
    % Torque
    % ScaledSatuMapTable.Electromagnetic_Torque                            =k_Radial^2 * k_Axial*  LabTable.  ;
%% Total Loss
    % ScaledSatuMapTable.Total_Loss                = ScaledSatuMapTable.Magnet_Loss +ScaledSatuMapTable.Banding_Loss+ScaledSatuMapTable.Stator_Copper_Loss+ScaledSatuMapTable.Iron_Loss;
end