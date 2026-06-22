%% Table of Contents
% def Path
% Get PartStruct
% Get Wire Element and Node ID
% Load Mat File From JplotReader  need Do prior -with python Code
%%
% JmagResultName='e10MS_ConductorModel_REF_Load~16_';
JmagResultPath='E:\KDH\e10\MSConductorModel\e10MS_ConductorModel.jfiles\e10MS_ConductorModel~6\e10MS_ConductorModel_SCL_Load~13'
% JmagResultName='e10MS_ConductorModel_SCL_Load~13';
[~,JmagResultName,~]=fileparts(JmagResultPath)
JmagResultDIR=extractBefore(JmagResultPath,'.jfiles');
[JmagPJTDIR,JmagPJTName,~]=fileparts(JmagResultDIR);
JmagPJTPath=fullfile(JmagPJTDIR,[JmagPJTName,'.jproj']);
%% Get PartStruct


% need 2 open Jproj
app=callJmag
app.Load(JmagPJTPath)
PartStruct=getJMAGDesignerPartStruct(app);
Lactive=150
PartTable=struct2table(PartStruct);
BoolTargetSlot=contains(PartTable.Name,'Slot1/')|contains(PartTable.Name,'Slot2/');
WireTable=PartTable(BoolTargetSlot,:);
WireTable = sortrows(WireTable,'Name'); 
LayerNumber=4
targetSlotNumber=2
targetPartIndex=LayerNumber*targetSlotNumber

%% Get Wire Element and Node ID
for SlotIndex=1:height(WireTable)
    WireIndex=WireTable.partIndex(SlotIndex);
    [ElementId{SlotIndex}, NodeID{SlotIndex},NodeTable{SlotIndex},delaunyObj{SlotIndex}]...
    =getMeshData(app,WireIndex);
end
% As Var 2 Table
WireTable.NodeTable=NodeTable';
WireTable.ElementId=ElementId';
WireTable.DT=delaunyObj';
% Backup
refWireTableBackup=WireTable;
%% Load Mat File From JplotReader 
%% DataStruct 읽고
% Mesh만들고
% Node Element 값일고
% 상호 연결하는 connection 만들고


% -python
% DataStruct=load('ref_e10_WirePeriodic_Load_18k_rgh~32_Case28_MagB.mat')
if 38100==getPCRDPPortNumber
    matFileList=findMatFiles('D:\KangDH\Emlab_emach\tools\jmag\jplotReader');
else
    matFileList=findMatFiles('Z:\01_Codes_Projects\git_fork_emach\tools\jmag\jplotReader');
end
MagBmatFileList=matFileList(contains(matFileList,JmagResultName)&contains(matFileList,'MagB')&~contains(matFileList,'backup','IgnoreCase',true));
MagBmatFileList = sort(MagBmatFileList); 
MagBmatFileList=MagBmatFileList(contains(MagBmatFileList,JmagResultName)&contains(MagBmatFileList,'28')&~contains(MagBmatFileList,'backup','IgnoreCase',true));

[~,MatfileNames,~]=fileparts(MagBmatFileList);
% for caseIndex=1:len(MatfileNames)


% WireTable의 결과를 저장할 셀 배열 선언
WireTableResults = cell(1, 30);


parpool;  % 병렬 풀 시작 (필요한 경우)

parfor caseIndex = 1:30  % 'parfor'를 사용하여 병렬 처리
    % 초기화
    WireTable = [];    
    % 데이터 로드
    DataStruct = load(MagBmatFileList{caseIndex});
    %% Mapping 2 WireStruct > WireTable
    WireTable = mappingB2Slot(DataStruct, refWireTableBackup);  % WireTable 생성
    WireTable = sortrows(WireTable, "Name", "ascend");  % 정렬
    WireTable = cart2polPartTable(WireTable);  % 좌표 변환    
    WireTable=removevars(WireTable,'object')
    % 결과를 셀 배열에 저장
    WireTableResults{caseIndex} = WireTable;
end

%% Mesh Export
% MPToolCSVFilePath='D:/KangDH/Emlab_emach/mlxperPJT/JEET/From38100/REF_e10_WTPM_PatternD_TS_case28.csv'
MPToolCSVFilePath='D:/KangDH/Emlab_emach/mlxperPJT/JEET/From38100/MPtools_SCL_e10_WTPM_PatternD_TS_case28.csv'
% [model, pdeTriElements, pdeNodes, pdeQuadElements, quadElementsId, combinedElements,FieldDataSteps]= nastran2PDEMesh(MPToolCSVFilePath,'mm');
 % [SCL_TSMesh,model,pdeTriElements,pdeNodes,pdeQuadElements]  = nastran2PDEMesh(MPToolCSVFilePath,'mm')
% save('SCL_TS_18krpm_case28_Mesh.mat','SCL_TSMesh');


%%
% for slotIndex = 1:height(WireTable)
allNodes=[]
for slotIndex = 1:8

    curNodes        =WireTable.NodeTable{slotIndex}.nodes;
    allNodes        =[allNodes;curNodes];
end
for slotIndex = 1:1

    curNodes        =WireTable.NodeTable{slotIndex}.nodes;

    curConnectivity =WireTable.DT{slotIndex}.ConnectivityList;
    % if all(WireTable.ZtimeTableByElerow{slotIndex}.nodes(:,1)==WireTable.NodeTable{slotIndex}.nodes(:,1))
    curMVPTab= rows2vars(WireTable.fieldzTimeTable{slotIndex});
    curNodesIDinJplot=curMVPTab.OriginalVariableNames;
    curMVPTab=removevars(curMVPTab,'OriginalVariableNames');
    % curMVP=   curMVPTab.Variables;
    curMVP=MagA_52(ismember(MagA_52(:,1),WireTable.NodeTable{slotIndex}.nodes(:,1)),4);
    % curMVP          =WireTable.ZtimeTableByElerow{slotIndex}.Step1;
    % [B_node, B_element] = calcFluxDensity(curNodes, curConnectivity, curMVP(:,timeIndex));
    % end


    curDTNodes=WireTable.DT{slotIndex}.Points;
    % if all(all(curDTNodes==WireTable.ZtimeTableByElerow{slotIndex}.nodes(:,2:3)))
    DT = WireTable.DT{slotIndex};  % X, Y 좌표
    % triplot(DT);
    % hold on;
    % % end
    % B_magnitude = sqrt(B_node(:,1).^2 + B_node(:,2).^2);
    % for timeIndex=52:52
    % trisurf(curConnectivity,DT.Points(:,1),DT.Points(:,2),curMVP(:,timeIndex));
    % hold on;
    % end
    scatter3(DT.Points(:,1),DT.Points(:,2),curMVP)
    hold on
    scatter3(pos(:,1),pos(:,2),a(:,2),'*r')
    % scatter3(DT.Points(:,1),DT.Points(:,2),curMVP(:,timeIndex))
end
MagA_52=DataStruct.MagA_52;

% DT.Points==;
DT.ConnectivityList
%%
% 각 슬롯별로 처리
% WireTable=refWireTableBackup
for slotIndex = 1:height(WireTable)

    originalNodeIDs=WireTable.NodeTable{slotIndex}.nodes(:,1);

    nodeIDMap = containers.Map(originalNodeIDs, 1:length(originalNodeIDs));  % 현재 슬롯의 nodeID를 1부터 시작하는 인덱스로 매핑



    % 1. 각 슬롯의 elementConnectivity에 있는 nodeID 수집
    elementConnectivity = WireTable.elementCentersTable{slotIndex}.elementConnectivity;
    allNodeIDs = unique(elementConnectivity(:));  % 현재 슬롯의 고유한 nodeID 수집    
    % 2. 고유한 nodeID에 대해 1부터 시작하는 번호로 매핑    
    % 3. elementConnectivity에 있는 nodeID를 매핑된 값으로 변환
    elementConnectivityMapped = zeros(size(elementConnectivity));
    for i = 1:numel(elementConnectivity)
        originalNodeID = elementConnectivity(i);  % 기존 nodeID
        mappedNodeID = nodeIDMap(originalNodeID);  % 매핑된 nodeID
        elementConnectivityMapped(i) = mappedNodeID;  % 매핑된 ID로 대체
    end
    
    % 4. WireTable의 elementConnectivity 업데이트
    WireTable.elementCentersTable{slotIndex}.elementConnectivity = elementConnectivityMapped;

  
      % 5. WireTable.NodeTable의 nodeID (nodes(:,1))도 매핑된 값으로 변환
    if all(allNodeIDs==originalNodeIDs)
     WireTable.NodeTable{slotIndex}.nodes(:,1)=   (1:length(allNodeIDs))';
    end
    % 6. WireTable.NodeTable 업데이트
    % 7. 매핑된 데이터로 triangulation 생성 및 시각화 (옵션)
    DT = triangulation(WireTable.elementCentersTable{slotIndex}.elementConnectivity, ...
                   WireTable.NodeTable{slotIndex}.nodes(:,2:3));  % X, Y 좌표
  
  
end

stepdata = extractJMAGFieldVectorFromMPtoolCSV(MPToolCSVFilePath, '16001')
csvFile=MPToolCSVFilePath
[model,pdeTriElements,pdeNodes,pdeQuadElements]  = nastran2PDEMesh(MPToolCSVFilePath);
