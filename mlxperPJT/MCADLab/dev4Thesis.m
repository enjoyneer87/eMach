
mcad(1)             =callMCAD
originModelIndex    =1
%% TODO List


% 38100 역할  -ssd
% 2018PC 역할 -ssd로 옮기기 (일단 C드라이브)

%[TB] mcad를 읽어서(파일열지않고 읽기)
% LAB 정보가져오기 
% 
% 4 HDEV 
% interp_Phi_dqh(Id, Iq): 주어진 전류 Id와 Iq에 대해 플럭스 
% interp_Ploss_dqh(Id, Iq, N0, exclude_models): 주어진 전류 Id, Iq, 회전 속도 N0에 대해 전력 손실을 보간합니다.
% get_Phi_dqh_mag_mean()
% interp_Tem_rip_dqh(Id, Iq): 주어진 Id, Iq에서의 토크 리플을 보간합니다.


% fitLdLqMapsFromMCADTable
% calcSpeedScaledLossFromMcadLinkTable
% calcTotalElecLossFromFitResultStr
% calcCurrentElecLossFromMcadLinkTable

% calculate_max_current(Id, Iq): 전류 벡터 Id와 Iq로부터 최대 전류를 계산합니다.
% calculate_voltage(Rs, Id, Iq, Phid, Phiq, ws): 주어진 저항 Rs, 전류 Id, Iq, 플럭스 
% calculate_torque(qs, p, Phid, Iq, Phiq, Id): 주어진 스테이터 위상 qs, 극 쌍 수 p, 플럭스 
% calculate_power(Ud, Id, Uq, Iq, qs): 입력 전압 Ud, Uq와 전류 Id, Iq, 스테이터 위상 qs를 이용해 입력 및 출력 전력을 계산합니다.


MotFilePath             =getCurrentMCADFilePath(mcad(1));

modifiedDataStruct      =getMcadActiveXTableFromMotFile(MotFilePath);
filteredTable           =getMCADLabDataFromMotFile(MotFilePath);

%
originLabLinkTable      = reNameLabTable2LabLink(filteredTable);
MCADLinkTable           = originLabLinkTable;



%% dev McADLinkTable Post(LUT)
MCADLinkTable       = originLabLinkTable    ;             
MachineData         = refLABBuildData       ;             
nTarget             = 500                   ; 
nTargetList         = [500:500:1500]        ;         
%%    
plotMultipleInterpSatuMapSubplots(@plotFitResult, MCADLinkTable);

[Ploss_dqh, scaledDataInfo] =interpLossFitResultSpeedFromMcadTable(MCADLinkTable,MachineData,nTargetList);
    

%% InterPolate 
[LdFitResult, LqFitResult,PMFit2DReulst,~] = fitLdLqMapsFromMCADTable(MCADLinkTable);
%McadLink Table 에서 손실 interpolation 함수 생성
% [PLossfitResult, scaledDataInfo] =interpLossdqhSpeedSetFromMCADTable(MCADLinkTable,MachineData,nTarget);
for nIndex=1:1:length(nTargetList)
    nTarget=nTargetList(nIndex);
    [Ploss_dqh(nIndex).fitResult,scaledDataInfo]=interpLossdqhSpeedSetFromMCADTable(MCADLinkTable,MachineData,nTarget);
end
    

%% Test
for nIndex=1:1:length(nTargetList)
plotFitResult(Ploss_dqh(nIndex).fitResult.Magnet.fitResult,scaledDataInfo.Magnet,0)
% hold on
end

%% EEC>EECLUTDq
% run
% comp_MTPA
% 

%% 1. DOE Code
% 
% 
% 
%% -PostCode
% 
% DOE  데이터정리
%     폴더정보 넣기
% 

HDEVModelPath='C:\Thesis\HDEV_Code3\OPD';


% file 리스트 가져오기
% MotFileList=findMOTFiles(HDEVModelPath)
[motFileList, DutyCycleMatFileList,ElecMatFileList,MatFileList] = getDriveMatList(HDEVModelPath);
[HDEVMotFile,HDEVMat]=getResultMotMatList(HDEVModelPath);





% 열기 코드
% OriginalLabTable 가져오고 체크
originLabTable=devGetMotoLabParameterData(mcad(originModelIndex));
% LabBuildData
[refLABBuildData]=getMCADBuildingData(mcad(originModelIndex));
MachineData = getMcadMachineDataFromMotFile(MotFilePath);


%% - TN Curve Plot
for MatFileIndex=1:length(HDEVMat.ElecMatFileList)
[~, ~]=plotMaxTorqueMotorCAD(HDEVMat.ElecMatFileList{MatFileIndex});
hold on
end
% Effimap 계산
plotTNContour('C:\Thesis\HDEV_Code3\OPD\HDEV_ob2o24i28si1f1.py.opd\Sensitivity\Design0600\HDEV_Model2_Design0600\Lab\MotorLAB_elecdata.mat')
figure(1)
plotAnyContourByNameinMotorcad(HDEVMat.ElecMatFileList{2},'Efficiency');
hold on
ax=gca;
ax.XLim=[0 18000];
ax.YLim=[0 1785.5];

%% - Duty Cycle Scatter


%% - 온도 Scatter

%% - 각 해석 Setting Getter 
% 결과로부터 Get

%% [WIP]2. scale
% 2024. 4 코드 변경 사항
% reference Mot File은 Open x
% ref MotFile에서 정보를 읽어서 Table형태로 변환, 
% [eetLUTdq호환은 이 테이블기준으로 추후 추가] 이게 훨씬 편할꺼같긴한데... 
% JMAG, Pyleecan

%% 입력창
% parentPath                      = 'Z:\Simulation\LabProject2023v3MDPI\ValidationDesign89Temp65';
% parentPath ='D:\KangDH\Optislang_Motorcad\HDEV_CODE2'
% parentPath ='D:\KangDH\Optislang_Motorcad\'
% parentPath                          = 'G:\KangDH\LabProj2023v3'    
% motMatFileListTable                 = getMotMatFileListTable(parentPath);
% NotScaled=find(~contains(motMatFileListTable.FileDir,'Scale'))
% NotScaledList=motMatFileListTable(NotScaled,:)


%%
% subParentPath                       =getSubPathStructList(parentPath)
% poleslotPath                        =getSubPathStructList([parentPath,'\',subParentPath{4}])
% poleslotPath                        =getSubPathStructList([parentPath,'\',subParentPath{5}])

%% FileTool
% getFileNameFromCell.mlx
                 
%% File 분류 

% MatFile
    % 용도별 Mat파일
         % FilePath나 이름, list추출 관련
        % getDOEResultMatFiles.m
        filename=matFileListMDPI.ElecMatFileList{1};
        varinfo=getVarInfoFromMatFile(filename) ;  
        % getNameCellofTableFormatInMatFile.m
        % getEnergyLossWhFromMatFileList.m
        % getMCADLabFilePath.m
        % getMCADLabDataFromMotFile.mlx
        % getMatDataFromMatFileList.m

        % 데이터 추출
        % getvarNameofMatfile.m
        % getVarNameFromMatfileByType.m
        % getVariablesHeight1FromMatFile.m

% MotFile
    % FilePath나 이름 관련
        % getCurrentMCADFilePath.m
        % getBuildListFromMotFileList.m -> backup
        % getMotResultLabDirFromMotFilePath.m
        % getMotResultDirFromMotFilePath.m
        % getMotFileDirNameFromBuildList.m

    
    % 데이터 추출
        % getDataFromMotFiles.m
        % getMcadActiveXTableFromMotFile.m
% MCAD Log File
        % getDataFromMessageLogFiles.m

%% 
%% BuildTable (ScalingMotTable 2 Build
parentPath              ='E:\KDH\8p48sVV\'          ; 
% parentPath              ='E:\KDH\230819_8P48S_Vtype';
% parentPath                ='Z:\Simulation\LabProj2023v3\230819_8P48S_Vtype'  ;             
motMatFileListTable       = getMotMatFileListTable(parentPath);

% %% Factor 정의
scaleFactor             =defScalingFactor(400/220,1,2,10,2,10,2);
BuildList               =getMCADData4ScalingList(parentPath,scaleFactor);
BuildTable              =struct2table(BuildList)                ;        

%% 2.1- ref Mot 파일 복사(SCFEA) 및 셋팅
DOEDIR               =fullfile(parentPath,'DOECubicSpline');
DOEDIR        =fullfile(parentPath,'DOE');

SLFEAMotFileParentPath=fullfile(parentPath,'SLFEA');
SLLAWMotFileParentPath=fullfile(parentPath,'SLLAW\');
deleteDir(SLLAWMotFileParentPath)
deleteDir(SLFEAMotFileParentPath)



%% Build Check
LabList_8p48sVV=MCADBuildList(DOEDIR);
LabList_8p48sVVBuildFromClass=LabList_8p48sVV.toTable;

%% SLFEA Mot 파일 복사 (SLFEA)
[SLFEAList2BuildFromMKList,SLFEAMotFileParentPath]=mkMCADScaledFilesFromList(LabList_8p48sVVBuildFromClass,'SLFEA',parentPath);


%% 2.2 MCAD에 맵구성
    %% - SCFEA 맵 구성 (FEA 해석)
%% Parallel Computation Code
motorCADManager = MCADLabManager(12, mergeSLFEATable);
motorCADManager.LabBuildSettingTable=defMcadLabBuildSetting();
motorCADManager=motorCADManager.processSLFEA();

% SLLAW 파일 복사
[SLLAWList2BuildFromClass,SLLAWMotFileParentPath]      =mkMCADScaledFilesFromList(SLFEALabListTable_8p48sVVBuildFromClass,'SLLAW',parentPath);

    %% - SCLaw 맵 구성 (땡겨오기)
%% 재시작할때 Lab Folder가 있는지 체크하고 없고, SatDate가 reMotFile 이랑 다르면 Build
runMCADIterativeProcess(SLFEAMotFileParentPath,BuildTable, 'SLFEA')
runMCADIterativeProcess(SLLAWMotFileParentPath,BuildTable, 'SLLAW')

%%  SLLAW vs SLFEA 검증 비교
Obj_SLLAWLabList_8p48sVV                               =MCADBuildList(SLLAWMotFileParentPath);
SLLAWLabListTable_8p48sVVBuildFromClass                =Obj_SLLAWLabList_8p48sVV.toTable;

Obj_SLFEALabList_8p48sVV                               =MCADBuildList(SLFEAMotFileParentPath);
SLFEALabListTable_8p48sVVBuildFromClass                =Obj_SLFEALabList_8p48sVV.toTable;
mergeSLFEATable      =mergeTables(BuildTable,SLFEALabListTable_8p48sVVBuildFromClass);

SLLAWBuildList               =getMCADData4ScalingList(SLLAWMotFileParentPath,scaleFactor);
SLFEABuildList               =getMCADData4ScalingList(SLFEAMotFileParentPath,scaleFactor);

% LabBuildData Check - MagLossCoeff_MotorLAB, 
% IronLossCalculationType - Bertotti로 변경필요
BuildList(2).BuildingData.LabBuildData
SLLAWBuildList(2).BuildingData.LabBuildData
SLFEABuildList(2).BuildingData.LabBuildData

SLLAWTable=SLLAWBuildList(2).refTable;
SLFEATable=SLFEABuildList(2).refTable;
SLLAWTable.Properties.Description='SL Law';
SLFEATable.Properties.Description='SL FEA';

% Plot
plotMultipleInterpSatuMapSubplots(@plotFitResult, SLLAWTable,SLFEATable);


DOE=createDOEstructFromMotFileList(mergeSLFEATable.MotFilePath);
FileList=getBuildMotHierList(mergeSLFEATable.MotFilePath)      ;

%  temp  명령어
mcad=callMCAD;
mcad.ShowMagneticContext()
% "Electromagnetic", "Thermal", "Generator", "Duty Cycle", and "Calibration".
mcad.SetMotorLABContext();
mcad.InitialiseTabNames;
mcad.DisplayScreen('Calculation');
%% 2.3 성능 계산
    %% TN curve
        %% TN계산 Setting 입력
% CalcTN & 효율맵(TN만 하고 DutyCycle로 그냥계산하면될꺼같은데)
% CalculateMagnetic_Lab - LabManager
refDriveSettingTable=defMcadLabCalcSetting();  
setMcadTableVariable(refDriveSettingTable,mcad);
tic
mcad.CalculateMagnetic_Lab();
toc % 10.512sec
mcad.ShowResultsViewer_Lab("Electromagnetic")
        %% [TB] Feasibility 판별 TN Curve 판별
% calcVehiclePerformance[del]

[MatFileData,motorSplitStruct]=tempPlotEfficiencyMapVehiclePerfom(Index4spmd,caseNum,DoEStruct,vehicleData,BasePointOutput,vehiclePerformData)
calcVehicleLateralDynamics
devLauchDoE4EffiVehicleDutyCycle
devLauchDoE4EfficiencyVehiclePerformance




%% Duty Cycle (EC)
% CalculateDutyCycle_Lab - LabManager 
% [DONE]calc DutyCycle in devReBuildDOE.mlx
%% EC계산 Setting 입력
TeslaSPlaidDutyCycleTable=defMcadDutyCycleSetting();
RefGearRatio  = findMcadTableVariableFromAutomationName(TeslaSPlaidDutyCycleTable, 'N_d_MotorLAB');
DutyCycleTable= updateMcadTableVariable(TeslaSPlaidDutyCycleTable,'N_d_MotorLAB',3);
setMcadTableVariable(DutyCycleTable,mcad);
tic
mcad.CalculateDutyCycle_Lab();
toc
% 29sec
[motFileList4Weight, DutyCycleMatFileList,ElecMatFileList,matFileList] = getDriveMatList(DOE8p48sVVPath)
fileList(3).DOE = getEnergyLossWhFromMatFileList(DutyCycleMatFileList, fileList(3).DOE);

%dev
xxxFileList(3).MatFile{loopIndex}.DutyMatData=calcDutyCycleLossFromMatFile(xxxFileList(3).MatFile{loopIndex}.DutyMatFilePath)
xxxFileList(3).DOE.(designN3).SumofTotalLoss=xxxFileList(3).MatFile{loopIndex}.DutyMatData;
      
%% 무게 계산
DOE8p48sVVScaledBuild = devExportWeightFromMCAD4DOEStrct(motFileList4Weight,TeslaSPlaidDutyCycleTable,40,10, mcad);

MotFilePath=getCurrentMCADFilePath(mcad)
modifiedData = getDataFromMotFiles(MotFilePath);

%% gear
computeMotorGearWeight2DOEStruct

    modifiedData(find(contains(modifiedData,'Weight')))
modifiedDataStruct = getMcadActiveXTableFromMotFile(MotFilePath)
a=modifiedDataStruct.Weight_Total
idx = contains(modifiedData,'Material_Weight_Notes')
idx = contains(modifiedData,'Mat_Weight_Notes')
Material_Weight_Notes=modifiedData(idx)
value=getValuesMotDatainCellFormat(Material_Weight_Notes)

%% AuVeCoDE Review


load('Z:\01_Codes_Projects\VehicleSystem\git_AuVECoDE\01_MAIN_functions\.dependency\dependency.mat')
Nodes = splitvars(G.Edges, 'EndNodes');
idx = find((Nodes.EndNodes_2==172));
coupledNode=Nodes.EndNodes_1(idx)
MainFunctionNode=G.Nodes.Short_Name(coupledNode)

[vehicle] = INITIALIZE_vehicle(Parameters);

%% 턴별로 생성한뒤, 동일전류밀도에서 큰거와 작은거 비교를 위해서는 다른 턴수로 전류범위를 맞춘뒤 비교가능
%% 정수 턴수별 AC Loss를 Plot해서 연속적인 함수로 Interpolation한뒤, Surrogate모델을 만드는것도 방법인듯

%% ref 2.4 Reference 모델과 비교 
    % - mass, EC, 
    % - Current Density
    

%% Scatter DOE


% FileList            =getBuildMotHierList(mergeSLFEATable)


% FileList
% filePath(1).motfilePath=MotFilePath;
% filePath(2).motfilePath=SLFEAMotFilePath;
% filePath(3).motfilePath=SLLAwScaledModelDirMotFilePath;


DesignNumber2XscatterDOEResultPerDOESet(DOE8p48sVVAGapScaledBuild, 'g', 'Scaled DOE8p48sVV reBuild', 1)
% scatterDOEResultPerDOESet(DOE8p48sVVAGapScaledBuild,'g','Scaled DOE8p48sVV reBuild',1); 
DesignNumber2XscatterDOEResultPerDOESet(DOE8p48sVVScaled,'g','Scaled DOE8P48sVV reBuild',0); 
DesignNumber2XscatterDOEResultPerDOESet(DOE8P48sVV,'g','DOE8P48sVV',0); 
%% If Efficiency Map
plotAnyContourByNameinMotorcad(matFileListMDPI.ElecMatFileList{3},'Power_Factor')