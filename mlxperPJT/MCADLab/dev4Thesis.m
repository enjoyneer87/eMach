
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
plotTNContour('C:\Thesis\HDEV_Code3\OPD\HDEV_ob2o24i28si1f1.py.opd\Sensitivity\Design0600\HDEV_Model2_Design0600\Lab\MotorLAB_elecdata.mat',)
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
        % getBuildListFromMotFileList.m
        % getMotResultLabDirFromMotFilePath.m
        % getMotResultDirFromMotFilePath.m
        % getMotFileDirNameFromBuildList.m

    
    % 데이터 추출
        % getDataFromMotFiles.m
        % getMcadActiveXTableFromMotFile.m
% MCAD Log File
        % getDataFromMessageLogFiles.m

%% 
% parentPath              ='E:\KDH\8p48sVV\DOECubicSpline'                   ; 
parentPath                ='Z:\Simulation\LabProj2023v3\230819_8P48S_Vtype'  ;             
motMatFileListTable       = getMotMatFileListTable(parentPath);

% %% Factor 정의
scaleFactor             =defScalingFactor(400/220,1,2,10,2,10,2);
BuildList=getMCADData4ScalingList(parentPath,scaleFactor);

% 
% %
% [BuilListMatFilePath,BuildList]        =checkBuildList(parentPath,1);
% %
% xxxFileList(1).path     =parentPath;
% for i=1:1
% xxxNewFileList(i)       =getBuildMotHierList(xxxFileList(i));
% end

% %% ref Mot 파일 가져오기
% FileIndex               =1;
% MotFilePath             =mkMotFilePathFromMotFileListTable(motMatFileListTable,FileIndex);
% %% GetMCADStruct From MotFile 4 Scale
% % [refLABBuildData]                       =getMCADBuildingData(mcad);
% [BuildingData,filteredTable]              = getMCADData4ScalingFromMotFile(MotFilePath);
% [SLScaledMachineData,SLLabTable,refTable] = scaleTable4LabTable(scaleFactor,filteredTable,BuildData);
% 


%% 2.1- ref Mot 파일 복사(SCFEA) 및 셋팅
% makeNewBuildListWithCheckLabBuild
% SLFEAMotFilePath= mkMCADFileFromRefPath(SLFEAMotFilePath,'SLLAW');
MotFileParentPath=[parentPath,'\','SLLAW'];
deleteDir(MotFileParentPath)


%% SLFEA Mot 파일 복사 (SLFEA)
[BuildList,MotFileParentPath]=mkMCADScaledFilesFromList(BuildList,'SLFEA',parentPath);


%% Parallel Computation Code
[BuildList,MotFileParentPath]=mkMCADScaledFilesFromList(BuildList,'SLLAW',parentPath);
motorCADManager = MCADLabManager(numMCAD, BuildList);
motorCADManager.LabBuildSettingTable=defMcadLabBuildSetting();
McadLabConditionVariable
settingLabBuildTable = defMcadLabBuildSetting()

motorCADManager.setupParallelPool();
motorCADManager.processFiles();
%% 턴별로 생성한뒤, 동일전류밀도에서 큰거와 작은거 비교를 위해서는 다른 턴수로 전류범위를 맞춘뒤 비교가능
%% 정수 턴수별 AC Loss를 Plot해서 연속적인 함수로 Interpolation한뒤, Surrogate모델을 만드는것도 방법인듯

% SLFEA가 먼저 없으면 SetVariable하고
% 있으면 SetVariable 하기

% FileList
filePath(1).motfilePath=MotFilePath;
filePath(2).motfilePath=SLFEAMotFilePath;
filePath(3).motfilePath=SLLAwScaledModelDirMotFilePath;
    
%% 2.2 MCAD에 맵구성
    %% - SCFEA 맵 구성 (FEA 해석)
    %% - SCLaw 맵 구성 (땡겨오기)


%% 2.3 성능 계산
% Build
% CalcTN
% CalculateMagnetic_Lab
setMcadTableVariable(refDriveSettingTable,mcad(3));
mcad(3).CalculateMagnetic_Lab();
% CalculateDutyCycle_Lab
TeslaSPlaidDutyCycleTable=defMcadDutyCycleSetting;
RefGearRatio  = findMcadTableVariableFromAutomationName(TeslaSPlaidDutyCycleTable, 'N_d_MotorLAB')
DutyCycleTable= updateMcadTableVariable(TeslaSPlaidDutyCycleTable,'N_d_MotorLAB',3)
setMcadTableVariable(DutyCycleTable,mcad(3))
mcad(3).CalculateDutyCycle_Lab();
    %% 무게 계산
DOE8p48sVVScaledBuild = devExportWeightFromMCAD4DOEStrct(motFileList4Weight,TeslaSPlaidDutyCycleTable,40,10, mcad);

    %% Duty Cycle (EC)
    % calc DutyCycle in devReBuildDOE.mlx

        %% EC계산 Setting 입력
    %% TN curve
        %% TN계산 Setting 입력
        %% Feasibility 판별 TN Curve 판별


%% ref 2.4 Reference 모델과 비교 
    % - mass, EC, 
    % - Current Density
    

