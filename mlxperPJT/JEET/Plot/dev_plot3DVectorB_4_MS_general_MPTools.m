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
% -python - 현재 문제있음
% DataStruct=load('ref_e10_WirePeriodic_Load_18k_rgh~32_Case28_MagB.mat')
if 38100==getPCRDPPortNumber
    matFileList=findMatFiles('D:\KangDH\Emlab_emach\tools\jmag\jplotReader');
    csvFileList=findCSVFiles('D:\KangDH\Emlab_emach\mlxperPJT\JEET\From38100\MPtools')
else
    matFileList=findMatFiles('Z:\01_Codes_Projects\git_fork_emach\tools\jmag\jplotReader');
    csvFileList=findCSVFiles('Z:\01_Codes_Projects\git_fork_emach\mlxperPJT\JEET\From38100\MPtools')
end
MagBmatFileList=matFileList(contains(matFileList,JmagResultName)&contains(matFileList,'MagB')&~contains(matFileList,'backup','IgnoreCase',true));
MagBmatFileList = sort(MagBmatFileList); 
MagBmatFileList=MagBmatFileList(contains(MagBmatFileList,JmagResultName)&contains(MagBmatFileList,'28')&~contains(MagBmatFileList,'backup','IgnoreCase',true));
[~,MatfileNames,~]=fileparts(MagBmatFileList);

MagACsvList=csvFileList(contains(csvFileList,'MSConductorModel_case28')&~contains(csvFileList,'backup','IgnoreCase',true));
% for caseIndex=1:len(MatfileNames)

MPToolCSVFilePath=MagACsvList{1}

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

    [modelObj,model,pdeTriElements,pdeNodes,pdeQuadElements,MVP]  = nastran2PDEMesh(MPToolCSVFilePath,'mm','11005');
    
     % 노드 좌표 추출 (p)
    p = DT.Points';  % 각 노드의 (x, y) 좌표, 전치시켜서 2xN 행렬
    
    % 삼각형 요소 추출 (t)
    t = DT.ConnectivityList';  % 삼각형 요소의 노드 인덱스, 전치시켜서 3xM 행렬
    
    % 경계 요소 추출 (e)
    edges = freeBoundary(DT);  % 자유 경계 (외부 경계) 요소 추출
    e = edges';  % 전치시켜서 2xL 행렬로 변환 (경계 요소)
    
    curMesh.p=[allslotNodex allslotNodey];
    curMesh.e=e;
    curMesh.t=t;
    
    a=emagmodel.Mesh
    [p,e,t]=a.meshToPet
    
    triplot(WireTable.DT{1})
    drawFluxDensity(curMesh, allMVP); 
    drawFluxDensity(curMesh, allMVP); 


end

%%
% for slotIndex = 1:height(WireTable)
allNodes=[];
for slotIndex = 1:8
    curNodes        =WireTable.NodeTable{slotIndex}.nodes;
    allNodes        =[allNodes;curNodes];
end

%% A 
timeSteps=fieldnames(MVP)
for timeIndex=1:len(timeSteps)
    
    for slotIndex = 1:8
    % Mesh
    curNodes = WireTable.NodeTable{slotIndex}.nodes;
    curNodesID = cellstr(num2str(curNodes(:,1)));
    curNodesID = strrep(curNodesID,' ','');
    curMVPTab = MVP.(timeSteps{timeIndex});

    % ismember에서 순서 일치시키기
    [isMemberMask, idxInCurMVPTab] = ismember(curNodesID, curMVPTab.NodeID);

    % curSlotMVPTab을 curNodesID의 순서에 맞게 가져오기
    curSlotMVPTab = curMVPTab(idxInCurMVPTab(isMemberMask), :);
    
    curDTNodes = WireTable.DT{slotIndex}.Points;
    DT = WireTable.DT{slotIndex};  % X, Y 좌표
    
    % DT.Points의 순서에 맞춰 curMVPTab의 순서를 변경하기 위해 좌표를 비교
    idxMatched = knnsearch([curMVPTab.PosX, curMVPTab.PosY], curDTNodes);

    % curMVPTab의 순서를 DT.Points와 맞추기
    curSlotMVPTabMatched = curMVPTab(idxMatched, :);
    curMVP = curSlotMVPTabMatched.vecz;  % vecz 값을 순서에 맞게 가져옴

    % Plot the mesh structure (you can enable this if needed)
    % triplot(DT);
    % hold on;

    curConnectivity = WireTable.DT{slotIndex}.ConnectivityList;

    % Scatter plot for MVP values (2D scatter with Z values)
    % scatter3(DT.Points(:,1), DT.Points(:,2), curMVP,'*r');

 

        % 노드 좌표 추출 (p)
    p = DT.Points';  % 각 노드의 (x, y) 좌표, 전치시켜서 2xN 행렬
    
    % 삼각형 요소 추출 (t)
    t = DT.ConnectivityList';  % 삼각형 요소의 노드 인덱스, 전치시켜서 3xM 행렬
    
    % 경계 요소 추출 (e)
    edges = freeBoundary(DT);  % 자유 경계 (외부 경계) 요소 추출
    e = edges';  % 전치시켜서 2xL 행렬로 변환 (경계 요소)
    
    curMesh.p=p;
    curMesh.e=e;
    curMesh.t=t;
    % [Babs, B] = calculate_B(curMVP*1000, curMesh);
    % drawFluxDensity(curMesh, curMVP*1000); 
     plotBContour(curMesh, curMVP*1000);
     % drawFluxDensity(curMesh, curMVP); 
        % 자속 밀도 계산
    % [Basbs, B_element,B_node] = calcFluxDensity(curMVP*1000, curMesh);
    % 
    % % trisurf (3D surface plot for B_magnitude)
    % trisurf(curConnectivity, DT.Points(:,1), DT.Points(:,2), B_node(1,:)');
    % 
    % % 요소 중심 계산 (옵션)
    % eleCenter = incenter(WireTable.DT{slotIndex});
    hold on;
     caxis([0 0.2]);  % 자속 밀도의 동적 범위로 설정
    colorbar;  % 색상 


 
        % 플롯을 한 단계씩 표시하기 위해 일시 정지 (선택 사항)
        pause(1);  % 1초 동안 정지 후 다음 time step으로 진행
    hold on
    end
end


    



% 원래의 MVP 데이터를 Scatter plot
scatter3(curMVPTab.PosX, curMVPTab.PosY, curMVPTab.vecz);
    triplot(DT);

for i = 1:num_elements
 
    % 이후의 계산 진행...
end
% 원래의 MVP 데이터를 Scatter plot
scatter3(curMVPTab.PosX, curMVPTab.PosY, curMVPTab.vecz);
%%
%% A 
for slotIndex = 1:4
    % Mesh
    curNodes        =WireTable.NodeTable{slotIndex}.nodes;
    curNodesID      =cellstr(num2str(curNodes(:,1)));
    curNodesID      =strrep(curNodesID,' ','');
    curMVPTab=MVP.step52;
    curSlotMVPTab=curMVPTab((ismember(curMVPTab.NodeID,curNodesID)),:);
    curDTNodes       =WireTable.DT{slotIndex}.Points;
    DT = WireTable.DT{slotIndex};  % X, Y 좌표
    % triplot(DT);
    hold on;
    curConnectivity =WireTable.DT{slotIndex}.ConnectivityList;
    % MVP
    curMVP=curSlotMVPTab.vecz;
    scatter3(DT.Points(:,1),DT.Points(:,2),curMVP)

    [B_node, B_element] = calcFluxDensity(DT, curMVP); 
    B_magnitude = sqrt(B_node(:,1).^2 + B_node(:,2).^2);
    % trisurf(curConnectivity,DT.Points(:,1),DT.Points(:,2),B_magnitude);
    eleCenter=incenter(WireTable.DT{slotIndex});

    hold on
end
scatter3(curMVPTab.PosX,curMVPTab.PosY,curMVPTab.vecz)
scatter3(curSlotMVPTab.PosX,curSlotMVPTab.PosY,curSlotMVPTab.vecz)

DT.ConnectivityList
%%
% 각 슬롯별로 처리
% WireTable=refWireTableBackup
for slotIndex = 1:height(WireTable)

    originalNodeIDs=WireTable.NodeTable{slotIndex}.nodes(:,1);
    nodeIDMap = containers.Map(originalNodeIDs, 1:length(originalNodeIDs));  % 현재 슬롯의 nodeID를 1부터 시작하는 인덱스로 매핑
    % 1. 각 슬롯의 elementConnectivity에 있는 nodeID 수집
    % 각 행의 모든 값이 originalNodeIDs에 포함된 삼각형 요소만 필터링
    isMemberMask = ismember(pdeTriElements, originalNodeIDs);
    
    % 각 삼각형의 모든 노드가 originalNodeIDs에 포함되어 있는지 확인
    rowsWithAllNodesInOriginal = all(isMemberMask, 1);  % 열 단위로 모두 포함되었는지 확인
    % 해당하는 삼각형 요소 선택 (3xN 행렬 유지)
    elementConnectivity = pdeTriElements(:, rowsWithAllNodesInOriginal);
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
    elementCentersTable{slotIndex}.elementConnectivity = elementConnectivityMapped;
      % 5. WireTable.NodeTable의 nodeID (nodes(:,1))도 매핑된 값으로 변환
    if all(allNodeIDs==originalNodeIDs)
     WireTable.NodeTable{slotIndex}.nodes(:,1)=   (1:length(allNodeIDs))';
    end
    % 6. WireTable.NodeTable 업데이트
    % 7. 매핑된 데이터로 triangulation 생성 및 시각화 (옵션)
    DT = triangulation(elementCentersTable{slotIndex}.elementConnectivity', ...
                   WireTable.NodeTable{slotIndex}.nodes(:,2:3));  % X, Y 좌표
end
