%[text:tableOfContents]{"heading":"목차"}
%[text] 비교 -
 ActiveXParameters = readMcadActiveX2Table("D:\KangDH\Thesis\e10\refModel\ActiveXParameters_ACLoss.txt")

%[text]  
%[text:table]{"columnWidths":[-1,102,-1,95,90,358],"ignoreHeader":true} %[text:anchor:M_7ffb]
%[text] |  |  | FEA (MS) |  | Law | FEA(TS) |
%[text] | --- | --- | --- | --- | --- | --- |
%[text] |  | ACLossHighFrequencyScaling\_Method | Improved | Improved |  |  |
%[text] | RefModel |  | [RefModel-FEA(MS)](internal:M_1cba) |  | x | o |
%[text] | SCModel |  | [SCModel-FEA(MS)](internal:M_6967) |  | o | o |
%[text:table]
%[text] RefModel
refModelPath="D:\KangDH\Thesis\e10\refModel\e10Turn6V261.mot";
[refModelDir,refModelMotFileName,FileExt]=fileparts(refModelPath);
% refPath='Z:\Simulation\JEETACLossValid_e10_v24\refModel\e10_UserRemesh.mot';
% refPath='F:\KDH\Thesis\JEET\e10\refModel\e10_UserRemesh.mot'
% refModelPath="D:\KangDH\Thesis\e4a\e4a_EMobility_IPM_User.mot"
% meshLoadTorquePath="D:\KangDH\Thesis\e4a\e4a_EMobility_IPM_User\FEResultsData\OnLoadTorque_result_1.mes"
% txtFEAPath=strcat(fileparts(meshLoadTorquePath),"\Mag_OnLoadTorque_result_1.txt")

fullpath = mfilename("fullpath");
MatDir='D:\KangDH\Thesis\e10';
% 경로와 파일명을 분리
[currentFolder, MfileName, b] = fileparts(fullpath);
MfileName=strrep(MfileName,'dev','');
mcad=callMCAD;
McadIndex=1;
speedList=[2000,4000,8000,16000]
mcad(McadIndex).LoadFromFile(refModelPath)

[~,CurrentMotFilePath_MotorLAB]=mcad.GetVariable('CurrentMotFilePath_MotorLAB')
if CurrentMotFilePath_MotorLAB==refModelPath
    [refLABBuildData]=getMCADBuildingData(mcad(1));
end
refLABBuildData.MotorCADGeo.WindingLayers
refLABBuildData.MotorCADGeo.Ratio_Bore

scalingFactorStruct=defScalingFactor(2,1,2,6,2,6,2);
k_Axial   =scalingFactorStruct.k_Axial   ;
k_Radial  =scalingFactorStruct.k_Radial  ;
k_Winding =scalingFactorStruct.k_Winding ;    
scalingFactorStruct.n_c =refLABBuildData.MotorCADGeo.WindingLayers; 
ScaledMachineData = SLScaleMachine(scalingFactorStruct,refLABBuildData.MotorCADGeo);

%[text] %[text:anchor:M_44a9] Scaling 
% mk File

ScaledBuildMotFilePath= mkMCADFileFromRefPath(refModelPath,'SLFEA');
dir(fileparts(ScaledBuildMotFilePath)) 
% ScaledBuildMotFilePath="D:\KangDH\Thesis\e10\SLFEA\e10Turn6V261SLFEA.mot"
mcad(McadIndex).LoadFromFile(ScaledBuildMotFilePath)
% mcad.SetVariable('GeometryParameterisation',1)
% mcad.SetVariable('MessageDisplayState',0)
% setMcadVariable(ScaledMachineData,mcad(McadIndex));
% [validGeo]=mcad(McadIndex).CheckIfGeometryIsValid(1);
% 

% 
% % Scale
% mcad(McadIndex).SaveToFile(ScaledBuildMotFilePath)
% % Check
% [~,CheckSLSOD]=mcad(McadIndex).GetVariable("Stator_Lam_Dia");
% if k_Radial==CheckSLSOD/refLABBuildData.MotorCADGeo.Stator_Lam_Dia
%     disp('Scale됨')
% end

%%
%% 선행 정보 추출
RMSCurrent    =460*k_Radial;
PhaseAdvance  =43.33;
StatorCurrentDemand_RMS_Lab=RMSCurrent;
PhaseAdvanceDemand_Lab     =PhaseAdvance;


[~,TorquePointsPerCycle]      =mcad.GetVariable('TorquePointsPerCycle');
[~,StatorSlotMeshLength]      =mcad.GetVariable('StatorSlotMeshLength');
[~,AirgapMeshPoints_layers]   =mcad.GetVariable('AirgapMeshPoints_layers');
[~,AirgapMeshPoints_mesh]     =mcad.GetVariable('AirgapMeshPoints_mesh');
%%
%[text] %[text:anchor:M_6967] ## SCModel - Hybrid

mcad.SetVariable('ProximityLossModel',1);
mcad.SetVariable('RMSCurrent',RMSCurrent);
mcad.SetVariable('PhaseAdvance',PhaseAdvance);

% FEA 결과 원본 경로 (DoMagneticCalculation 후 결과가 저장되는 폴더)
[~,curModelPath]=mcad.GetVariable('CurrentMotFilePath_MotorLAB')
[curModelDir,curModelMotFileName,curFileExt]=fileparts(curModelPath);
FEA_SRC_DIR=fullfile(fullfile(curModelDir,curModelMotFileName),'FEResultsData')

% 백업 루트 폴더
FEA_BACKUP_ROOT = fullfile(fileparts(FEA_SRC_DIR), 'FEResultsData_backup');
ActiveXParameters = readMcadActiveX2Table("D:\KangDH\Thesis\e10\refModel\ActiveXParameters_ACLoss.txt");
% ──────────────────────────────────────────────────────────────
[~,HairpinConductors_FEA] = mcad.GetVariable('HairpinConductors_FEA');    
% mcad.SetVariable('ProximityLossModel',1) % Hybrid
[~,ProximityLossModel]    = mcad.GetVariable('ProximityLossModel');   

for SpeedIndex=1:length(speedList)
    mcad.SetVariable('ShaftSpeed',speedList(SpeedIndex));
    mcad.DoMagneticCalculation()
    % ── FEA 결과 + MessageLogs 백업 ───────────────────────────────
    speedRPM = speedList(SpeedIndex);
    backupMCADFEAResult(FEA_SRC_DIR, FEA_BACKUP_ROOT, sprintf('Speed_%dRPM', speedRPM));
    
 
    % mcad.SetVariable('HairpinConductors_FEA',0);    
    if ProximityLossModel==1 %Hybrid
        [ACLossTable,HybridConductorSkinDepthCell{SpeedIndex},Conductor_DCLossEmagMCADCell{SpeedIndex},DCConductorLoss_Armature_ACell{SpeedIndex}]=getMCADHybridMethodLoss(mcad)
        ACLossTableCell{SpeedIndex}=ACLossTable;
        [~,ACLoss_Hybrid_Total{SpeedIndex}           ] =mcad.GetVariable('ACLoss_Hybrid_Total')            ; 
        [~,ACLoss_Hybrid_Prox_Total{SpeedIndex}]=mcad.GetVariable('ACLoss_Hybrid_Prox_Total');
        [~,ACLoss_Hybrid_SkinEffect_Total{SpeedIndex}] =mcad.GetVariable('ACLoss_Hybrid_SkinEffect_Total') ;             
        [~,ACLosses_BundleHeight              ]=mcad.GetVariable('ACLosses_BundleHeight'     )
        [~,ACLosses_BundleWidth               ]=mcad.GetVariable('ACLosses_BundleWidth'      )
        [~,ACLosses_BundleAspectRatio         ]=mcad.GetVariable('ACLosses_BundleAspectRatio')
        [~,ACLosses_BundleSize_CalcMethod     ]=mcad.GetVariable('ACLosses_BundleSize_CalcMethod')   
    elseif ProximityLossModel==2 % single Slot
        ACLossTableCell{SpeedIndex}=getMcadTableVariable(ActiveXParameters,mcad);
    elseif ProximityLossModel==3 % Full        
        ACLossTableCell{SpeedIndex}=getMcadTableVariable(ActiveXParameters,mcad);
    end
end

% if HairpinConductors_FEA==1 %Hybrid
Hybrid=struct();
Hybrid.('ACLoss_Hybrid_Total'           )=ACLoss_Hybrid_Total           ;
Hybrid.('ACLoss_Hybrid_Prox_Total')         =ACLoss_Hybrid_Prox_Total;
Hybrid.('ACLoss_Hybrid_SkinEffect_Total')=ACLoss_Hybrid_SkinEffect_Total;
Hybrid.('Conductor_DCLossEmagMCAD')                        =Conductor_DCLossEmagMCADCell         ;                                 
Hybrid.('DCConductorLoss_Armature_A')                      =DCConductorLoss_Armature_ACell       ; 

SLModelHybrid=Hybrid
varName2SaveList{1}='SLModelHybrid';

% elseif HairpinConductors_FEA==2 % single Slot


%1D Table
%2D Table
%3D Table
%4D Table
% Hybrid.('ConductorSkinDepth')                              =HybridConductorSkinDepth       ;                   

%[text] 
% plot(speedList,[Hybrid.ACConductorLoss_MagneticMethod_Total{:}],'DisplayName','Hybrid')

%%
%[text] ## SCModel - FEA(TS)
mcad(McadIndex).LoadFromFile(ScaledBuildMotFilePath)
RMSCurrent    =460*k_Radial;
PhaseAdvance  =43.33;
StatorCurrentDemand_RMS_Lab=RMSCurrent;
PhaseAdvanceDemand_Lab     =PhaseAdvance;

mcad.SetVariable('ProximityLossModel',3);
mcad.SetVariable('RMSCurrent',RMSCurrent);
mcad.SetVariable('PhaseAdvance',PhaseAdvance);
mcad.SetVariable('TorquePointsPerCycle',128);


[~,curModelPath]=mcad.GetVariable('CurrentMotFilePath_MotorLAB')
[curModelDir,curModelMotFileName,curFileExt]=fileparts(curModelPath);
FEA_SRC_DIR=fullfile(fullfile(curModelDir,curModelMotFileName),'FEResultsData')


% 백업 루트 폴더
FEA_BACKUP_ROOT = fullfile(fileparts(FEA_SRC_DIR), 'FEResultsData_backup');
ActiveXParameters = readMcadActiveX2Table("D:\KangDH\Thesis\e10\refModel\ActiveXParameters_ACLoss.txt");
[~,ProximityLossModel]    = mcad.GetVariable('ProximityLossModel');  
[~,HairpinConductors_FEA] = mcad.GetVariable('HairpinConductors_FEA');    

for SpeedIndex=1:length(speedList)
    mcad.SetVariable('ShaftSpeed',speedList(SpeedIndex));
    mcad.DoMagneticCalculation()
    % ── FEA 결과 + MessageLogs 백업 ───────────────────────────────
    speedRPM = speedList(SpeedIndex);
    backupMCADFEAResult(FEA_SRC_DIR, FEA_BACKUP_ROOT, sprintf('Speed_%dRPM', speedRPM));

    % ──────────────────────────────────────────────────────────────
    % mcad.SetVariable('HairpinConductors_FEA',0);    
    if ProximityLossModel==1 %Hybrid
        [ACLossTable,HybridConductorSkinDepthCell{SpeedIndex},Conductor_DCLossEmagMCADCell{SpeedIndex},DCConductorLoss_Armature_ACell{SpeedIndex}]=getMCADHybridMethodLoss(mcad)
        ACLossTableCell{SpeedIndex}=ACLossTable;
        [~,ACLoss_Hybrid_Total{SpeedIndex}           ] =mcad.GetVariable('ACLoss_Hybrid_Total')            ; 
        [~,ACLoss_Hybrid_Prox_Total{SpeedIndex}]=mcad.GetVariable('ACLoss_Hybrid_Prox_Total');
        [~,ACLoss_Hybrid_SkinEffect_Total{SpeedIndex}] =mcad.GetVariable('ACLoss_Hybrid_SkinEffect_Total') ;             
        [~,ACLosses_BundleHeight              ]=mcad.GetVariable('ACLosses_BundleHeight'     )
        [~,ACLosses_BundleWidth               ]=mcad.GetVariable('ACLosses_BundleWidth'      )
        [~,ACLosses_BundleAspectRatio         ]=mcad.GetVariable('ACLosses_BundleAspectRatio')
        [~,ACLosses_BundleSize_CalcMethod     ]=mcad.GetVariable('ACLosses_BundleSize_CalcMethod')   
    elseif ProximityLossModel==2 % single Slot
        ACLossTableCell{SpeedIndex}=getMcadTableVariable(ActiveXParameters,mcad);
    elseif ProximityLossModel==3 % Full        
        ACLossTableCell{SpeedIndex}=getMcadTableVariable(ActiveXParameters,mcad);
    end
end

if ProximityLossModel==1 %Hybrid
Hybrid=struct();
Hybrid.('ACLoss_Hybrid_Total'           )=ACLoss_Hybrid_Total           ;
Hybrid.('ACLoss_Hybrid_Prox_Total')         =ACLoss_Hybrid_Prox_Total;
Hybrid.('ACLoss_Hybrid_SkinEffect_Total')=ACLoss_Hybrid_SkinEffect_Total;
Hybrid.('Conductor_DCLossEmagMCAD')                        =Conductor_DCLossEmagMCADCell         ;                                 
Hybrid.('DCConductorLoss_Armature_A')                      =DCConductorLoss_Armature_ACell       ; 
SLModelHybrid=Hybrid
varName2SaveList{end+1}='SLModelHybrid';
elseif ProximityLossModel==3
FullFEATS=struct();
FullFEATS.('ACLossTable')=ACLossTableCell;
[~,ConductorLoss]                  =mcad.GetVariable('ConductorLoss');
[~,DCConductorLoss_Armature_A]                 =mcad.GetVariable('DCConductorLoss_Armature_A');
% get Resistance Data
[~,ArmatureWindingResistancePh]                  =mcad.GetVariable('ArmatureWindingResistancePh');
[~,Resistance_MotorLAB          ]              =mcad.GetVariable('Resistance_MotorLAB');
[~,EndWindingResistance_Lab     ]              =mcad.GetVariable('EndWindingResistance_Lab');
ResistanceActivePart=Resistance_MotorLAB-EndWindingResistance_Lab;
% Calculate total DC losses for the active part
DCLossTotal = calcDCLoss(Resistance_MotorLAB, RMSCurrent);
DCLossActiveEndPart = calcDCLoss(EndWindingResistance_Lab, RMSCurrent);
DCLossActivePart = calcDCLoss(ResistanceActivePart, RMSCurrent);


end

FullFEATS=struct();
FullFEATS.('ACLossTable')=ACLossTableCell;
SLModelTS=FullFEATS
varName2SaveList{end+1}='SLModelTS';

for SpeedIndex=1:length(speedList) 
    %% Active Length Only - DC+AC 
    ACLoss_FEA_OnLoad_PerTurn=getValueFromMCADTablebyName(SLModelTS.ACLossTable{SpeedIndex},'ACLoss_FEA_OnLoad_PerTurn')
    ACLoss_FEA_OnLoad_PerTurn_Sum{SpeedIndex}=sum(ACLoss_FEA_OnLoad_PerTurn.ACLoss_FEA_OnLoad_PerTurn)/1000
    ACLoss_FEA_activePartSum{SpeedIndex}=ACLoss_FEA_OnLoad_PerTurn_Sum{SpeedIndex}-DCLossActivePart/1000
    % AC Loss - Active Part
    ACLoss_FEA_OnLoad_Total=getValueFromMCADTablebyName(SLModelTS.ACLossTable{SpeedIndex},'ACLoss_FEA_OnLoad_Total')
    ACLoss_FEA_OnLoad_Total_inkW{SpeedIndex}=ACLoss_FEA_OnLoad_Total.ACLoss_FEA_OnLoad_Total/1000
    % ACLoss_FEA_activePartTotal{SpeedIndex}=ACLoss_FEA_OnLoad_Total_inkW{SpeedIndex}-DCLossActivePart/1000
end
SCACLoss_FEA_activePartSum=ACLoss_FEA_activePartSum
%[text] %[text:anchor:M_1cba] ## RefModel - FEA(MS)
RMSCurrent    =460;
PhaseAdvance  =43.33;
mcad.LoadFromFile(refModelPath)
mcad.SetVariable('ProximityLossModel',1);
mcad.SetVariable('RMSCurrent',RMSCurrent);
mcad.SetVariable('PhaseAdvance',PhaseAdvance);

[~,curModelPath]=mcad.GetVariable('CurrentMotFilePath_MotorLAB')
[curModelDir,curModelMotFileName,curFileExt]=fileparts(curModelPath);
FEA_SRC_DIR=fullfile(fullfile(curModelDir,curModelMotFileName),'FEResultsData')


% 백업 루트 폴더
FEA_BACKUP_ROOT = fullfile(fileparts(FEA_SRC_DIR), 'FEResultsData_backup');

ActiveXParameters = readMcadActiveX2Table("D:\KangDH\Thesis\e10\refModel\ActiveXParameters_ACLoss.txt");
mcad.SetVariable('ProximityLossModel',1) % Hybrid
[~,ProximityLossModel]    = mcad.GetVariable('ProximityLossModel');  
[~,HairpinConductors_FEA] = mcad.GetVariable('HairpinConductors_FEA');    

for SpeedIndex=1:length(speedList)
    mcad.SetVariable('ShaftSpeed',speedList(SpeedIndex));
    mcad.DoMagneticCalculation()
    % ── FEA 결과 + MessageLogs 백업 ───────────────────────────────
    speedRPM = speedList(SpeedIndex);
    backupMCADFEAResult(FEA_SRC_DIR, FEA_BACKUP_ROOT, sprintf('Speed_%dRPM', speedRPM));
    
    % ──────────────────────────────────────────────────────────────
    % mcad.SetVariable('HairpinConductors_FEA',0);    
    if ProximityLossModel==1 %Hybrid
        [ACLossTable,HybridConductorSkinDepthCell{SpeedIndex},Conductor_DCLossEmagMCADCell{SpeedIndex},DCConductorLoss_Armature_ACell{SpeedIndex}]=getMCADHybridMethodLoss(mcad)
        ACLossTableCell{SpeedIndex}=ACLossTable;
        [~,ACLoss_Hybrid_Total{SpeedIndex}           ] =mcad.GetVariable('ACLoss_Hybrid_Total')            ; 
        [~,ACLoss_Hybrid_Prox_Total{SpeedIndex}]=mcad.GetVariable('ACLoss_Hybrid_Prox_Total');
        [~,ACLoss_Hybrid_SkinEffect_Total{SpeedIndex}] =mcad.GetVariable('ACLoss_Hybrid_SkinEffect_Total') ;             
        [~,ACLosses_BundleHeight              ]=mcad.GetVariable('ACLosses_BundleHeight'     )
        [~,ACLosses_BundleWidth               ]=mcad.GetVariable('ACLosses_BundleWidth'      )
        [~,ACLosses_BundleAspectRatio         ]=mcad.GetVariable('ACLosses_BundleAspectRatio')
        [~,ACLosses_BundleSize_CalcMethod     ]=mcad.GetVariable('ACLosses_BundleSize_CalcMethod')   
    elseif ProximityLossModel==2 % single Slot
        ACLossTableCell{SpeedIndex}=getMcadTableVariable(ActiveXParameters,mcad);
    elseif ProximityLossModel==3 % Full        
        ACLossTableCell{SpeedIndex}=getMcadTableVariable(ActiveXParameters,mcad);
    end
end
% if HairpinConductors_FEA==1 %Hybrid
Hybrid=struct();
Hybrid.('ACLoss_Hybrid_Total'           )=ACLoss_Hybrid_Total           ;
Hybrid.('ACLoss_Hybrid_Prox_Total')         =ACLoss_Hybrid_Prox_Total;
Hybrid.('ACLoss_Hybrid_SkinEffect_Total')=ACLoss_Hybrid_SkinEffect_Total;
Hybrid.('Conductor_DCLossEmagMCAD')                        =Conductor_DCLossEmagMCADCell         ;                                 
Hybrid.('DCConductorLoss_Armature_A')                      =DCConductorLoss_Armature_ACell       ; 


refModelHybrid=Hybrid
varName2SaveList{end+1}='refModelHybrid';

%[text] ## RefModel-FEA(TS)
mcad.SetVariable('ProximityLossModel',3);
mcad.SetVariable('RMSCurrent',RMSCurrent);
mcad.SetVariable('PhaseAdvance',PhaseAdvance);
mcad.SetVariable('TorquePointsPerCycle',128);

[~,curModelPath]=mcad.GetVariable('CurrentMotFilePath_MotorLAB')
[curModelDir,curModelMotFileName,curFileExt]=fileparts(curModelPath);
FEA_SRC_DIR=fullfile(fullfile(curModelDir,curModelMotFileName),'FEResultsData')


% 백업 루트 폴더
FEA_BACKUP_ROOT = fullfile(fileparts(FEA_SRC_DIR), 'FEResultsData_backup');
ActiveXParameters = readMcadActiveX2Table("D:\KangDH\Thesis\e10\refModel\ActiveXParameters_ACLoss.txt");
[~,ProximityLossModel]    = mcad.GetVariable('ProximityLossModel');  
[~,HairpinConductors_FEA] = mcad.GetVariable('HairpinConductors_FEA');    

for SpeedIndex=1:length(speedList)
    mcad.SetVariable('ShaftSpeed',speedList(SpeedIndex));
    mcad.DoMagneticCalculation()
    % ── FEA 결과 + MessageLogs 백업 ───────────────────────────────
    speedRPM = speedList(SpeedIndex);
    backupMCADFEAResult(FEA_SRC_DIR, FEA_BACKUP_ROOT, sprintf('Speed_%dRPM', speedRPM));

    % ──────────────────────────────────────────────────────────────
    % mcad.SetVariable('HairpinConductors_FEA',0);    
    if ProximityLossModel==1 %Hybrid
        [ACLossTable,HybridConductorSkinDepthCell{SpeedIndex},Conductor_DCLossEmagMCADCell{SpeedIndex},DCConductorLoss_Armature_ACell{SpeedIndex}]=getMCADHybridMethodLoss(mcad)
        ACLossTableCell{SpeedIndex}=ACLossTable;
        [~,ACLoss_Hybrid_Total{SpeedIndex}           ] =mcad.GetVariable('ACLoss_Hybrid_Total')            ; 
        [~,ACLoss_Hybrid_Prox_Total{SpeedIndex}]=mcad.GetVariable('ACLoss_Hybrid_Prox_Total');
        [~,ACLoss_Hybrid_SkinEffect_Total{SpeedIndex}] =mcad.GetVariable('ACLoss_Hybrid_SkinEffect_Total') ;             
        [~,ACLosses_BundleHeight              ]=mcad.GetVariable('ACLosses_BundleHeight'     )
        [~,ACLosses_BundleWidth               ]=mcad.GetVariable('ACLosses_BundleWidth'      )
        [~,ACLosses_BundleAspectRatio         ]=mcad.GetVariable('ACLosses_BundleAspectRatio')
        [~,ACLosses_BundleSize_CalcMethod     ]=mcad.GetVariable('ACLosses_BundleSize_CalcMethod')   
    elseif ProximityLossModel==2 % single Slot
        ACLossTableCell{SpeedIndex}=getMcadTableVariable(ActiveXParameters,mcad);
    elseif ProximityLossModel==3 % Full        
        ACLossTableCell{SpeedIndex}=getMcadTableVariable(ActiveXParameters,mcad);
    end
end

if ProximityLossModel==1 %Hybrid
Hybrid=struct();
Hybrid.('ACLoss_Hybrid_Total'           )=ACLoss_Hybrid_Total           ;
Hybrid.('ACLoss_Hybrid_Prox_Total')         =ACLoss_Hybrid_Prox_Total;
Hybrid.('ACLoss_Hybrid_SkinEffect_Total')=ACLoss_Hybrid_SkinEffect_Total;
Hybrid.('Conductor_DCLossEmagMCAD')                        =Conductor_DCLossEmagMCADCell         ;                                 
Hybrid.('DCConductorLoss_Armature_A')                      =DCConductorLoss_Armature_ACell       ; 
refModelHybrid=Hybrid
varName2SaveList{end+1}='refModelHybrid';
elseif ProximityLossModel==3
FullFEATS=struct();
FullFEATS.('ACLossTable')=ACLossTableCell;
[~,ConductorLoss]                  =mcad.GetVariable('ConductorLoss');
[~,DCConductorLoss_Armature_A]                 =mcad.GetVariable('DCConductorLoss_Armature_A');
% get Resistance Data
[~,ArmatureWindingResistancePh]                  =mcad.GetVariable('ArmatureWindingResistancePh');
[~,Resistance_MotorLAB          ]              =mcad.GetVariable('Resistance_MotorLAB');
[~,EndWindingResistance_Lab     ]              =mcad.GetVariable('EndWindingResistance_Lab');
ResistanceActivePart=Resistance_MotorLAB-EndWindingResistance_Lab;
% Calculate total DC losses for the active part
RMSCurrent=460
DCLossTotal = calcDCLoss(Resistance_MotorLAB, RMSCurrent);
DCLossActiveEndPart = calcDCLoss(EndWindingResistance_Lab, RMSCurrent);
DCLossActivePart = calcDCLoss(ResistanceActivePart, RMSCurrent);


end

FinalLossList={
    'StatorIronLoss_Total_Adj',
    'RotorIronLoss_Total_Adj',
    'MagnetLoss_Adj',
    'Loss_[Windage]'};


%%
% McadWattsTable=getMCADWattsTable(mcad)
% McadWattsTable = filterMCADTableZeroValue(McadWattsTable)
% McadFinalLossWattsTable=filterMCADTable(McadWattsTable,FinalLossList,'exact')
% McadFinalLossWattsTable=getMcadTableVariable(McadFinalLossWattsTable,mcad)
% McadFinalLossWattsTable = convertMCADTableCurrentValueToDouble(McadFinalLossWattsTable)
% McadFinalLossWattsTable = filterMCADTableZeroValue(McadFinalLossWattsTable)
% McadFinalLossWattsTable = convertMcadTable2UnvTable(McadFinalLossWattsTable)
% totalLoss=sum(McadFinalLossWattsTable.doubleValue)
% totalLossinKw=totalLoss/1000
% TotalWindingLoss=DCLossActiveEndPart/1000+ACLoss_FEA_OnLoad_PerTurn_Sum
% 
% % Calculate and display the total losses
% totalLosses = TotalWindingLoss + totalLossinKw;


disp(['Total Losses: ', num2str(totalLosses), ' kW']);
refModelTS=FullFEATS
varName2SaveList{end+1}='refModelTS';

clear ACLoss_FEA_OnLoad_Total_inkW
clear ACLoss_FEA_OnLoad_PerTurn_Sum
clear ACLoss_FEA_activePartTotal
for SpeedIndex=1:length(speedList) 
    %% Active Length Only - DC+AC 
    ACLoss_FEA_OnLoad_PerTurn=getValueFromMCADTablebyName(refModelTS.ACLossTable{SpeedIndex},'ACLoss_FEA_OnLoad_PerTurn')
    ACLoss_FEA_OnLoad_PerTurn_Sum{SpeedIndex}=sum(ACLoss_FEA_OnLoad_PerTurn.ACLoss_FEA_OnLoad_PerTurn)/1000
    ACLoss_FEA_activePartSum{SpeedIndex}=ACLoss_FEA_OnLoad_PerTurn_Sum{SpeedIndex}-DCLossActivePart/1000
    % AC Loss - Active Part
    ACLoss_FEA_OnLoad_Total=getValueFromMCADTablebyName(refModelTS.ACLossTable{SpeedIndex},'ACLoss_FEA_OnLoad_Total')
    ACLoss_FEA_OnLoad_Total_inkW{SpeedIndex}=ACLoss_FEA_OnLoad_Total.ACLoss_FEA_OnLoad_Total/1000
    % ACLoss_FEA_activePartTotal{SpeedIndex}=ACLoss_FEA_OnLoad_Total_inkW{SpeedIndex}-DCLossActivePart/1000
end
Ref_ACLoss_FEA_activePartSum=ACLoss_FEA_activePartSum

%[text] ## SCModel-Law

%[text] ## Hyb Plot
% plot(speedList,[refModelHybrid.ACLoss_Hybrid_Prox_Total{:}]/1000,'DisplayName','refModelHybridProx','LineStyle','--','Color','blue')
figure(1)
subplot(3,1,1)

plot(speedList,[Ref_ACLoss_FEA_activePartSum{:}],'DisplayName','refModelTS','LineStyle',':','Marker','*','color','blue')
hold on
plot(speedList,[refModelHybrid.ACLoss_Hybrid_Total{:}]/1000,'DisplayName','refModelHybrid','LineStyle','-','Color','blue')
Ref_TS_Hyb_Ratio=[Ref_ACLoss_FEA_activePartSum{:}]./([refModelHybrid.ACLoss_Hybrid_Total{:}]/1000),
% plot(speedList,[refModelHybrid.ACLoss_Hybrid_SkinEffect_Total{:}]/1000,'DisplayName','refModelHybridSkin','LineStyle','--','Color','cyan')
% plot(speedList,[SLModelHybrid.ACLoss_Hybrid_Prox_Total{:}]/1000,'DisplayName','SCModelHybridProx','LineStyle','--','Color','red')
subplot(3,1,2)
% plot(speedList(1:2)*4,[SLModelHybrid.ACLoss_Hybrid_Total{1:2}]/1000,'DisplayName','SCModelHybrid','LineStyle','-','Marker','*','Color','red')
plot(speedList,[SLModelHybrid.ACLoss_Hybrid_Total{:}]/1000,'DisplayName','SCModelHybrid','LineStyle','-','Marker','*','Color','red')

hold on
% plot(speedList,[SLModelHybrid.ACLoss_Hybrid_SkinEffect_Total{:}]/1000,'DisplayName','SCModelHybridSkin','LineStyle','--','Color','magenta')


plot(speedList,[SCACLoss_FEA_activePartSum{}],'DisplayName','SCModelTS','LineStyle',':','Marker','*','color','magenta')
SC_TS_Hyb_Ratio=[SCACLoss_FEA_activePartSum{:}]./([SLModelHybrid.ACLoss_Hybrid_Total{:}]/1000),

subplot(3,1,3)

plot(speedList,SC_TS_Hyb_Ratio,'DisplayName','SC_TS_Hyb_Ratio')
hold on
plot(speedList,Ref_TS_Hyb_Ratio,'DisplayName','Ref_TS_Hyb_Ratio')


HybACRatio=[SLModelHybrid.ACLoss_Hybrid_Total{:}]./[refModelHybrid.ACLoss_Hybrid_Total{:}]
HybProxACRatio=[SLModelHybrid.ACLoss_Hybrid_Prox_Total{:}]./[refModelHybrid.ACLoss_Hybrid_Prox_Total{:}]
HybSkinACRatio=[SLModelHybrid.ACLoss_Hybrid_SkinEffect_Total{:}]./[refModelHybrid.ACLoss_Hybrid_SkinEffect_Total{:}]

% Prepare data for saving results
saveDataPath = fullfile(FEA_BACKUP_ROOT, 'Results.mat');
save(saveDataPath, 'refModelTS,','SLModelHybrid', 'refModelHybrid', 'HybACRatio', 'HybProxACRatio', 'HybSkinACRatio');

% TS Plot
plot(speedList,refModelTS.ACLossTable{:})
refModelTS.ACLossTable{1}.AutomationName
ModelBuildPoints_Current_Lab= getValueFromMCADTablebyName(refModelTS.ACLossTable{1},'');
%% plot(speedList,[SLModelHybrid.ACConductorLoss_MagneticMethod_Total{:}],'DisplayName','SLModelHybrid')
% plot(speedList,HybACRatio,'DisplayName','Scaling Ratio of AC Loss');
%%

% mcad.LoadFEAResult(meshLoadTorquePath,1)
% [~,TorquePointsPerCycle]=mcad.GetVariable('TorquePointsPerCycle')
% mcad.SaveFEAData(txtFEAPath,1,TorquePointsPerCycle, 'RegCode,Bx,By,A,J,Je','',',')
% for caseIndex=1:1
%     HybridSetting           =mkMCADHybridACMethodCase(caseIndex)
%     MCADResultSet(caseIndex)=doNgetMCADLossPerSpeed(mcad,speedList,HybridSetting);
% end


%[appendix]{"version":"1.0"}
%---
%[metadata:view]
%   data: {"layout":"inline"}
%---
