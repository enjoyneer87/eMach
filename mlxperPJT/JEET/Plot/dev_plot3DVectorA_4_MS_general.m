%% Table of Contents
% def Path
% Get PartStruct
% Get Wire Element and Node ID
% Load Mat File From JplotReader  need Do prior -with python Code
%%
% JmagResultName='e10MS_ConductorModel_REF_Load~16_';
JmagResultPath='E:\KDH\e10\MSConductorModel\e10MS_ConductorModel.jfiles\e10MS_ConductorModel~6\e10MS_ConductorModel_SCL_Load~13'
% JmagResultPath='F:\KDH\KDH\SCL_e10_WTPM_PatternD_R1_4k.jfiles\SC_e10_WirePeriodic~9\SC_e10_WirePeriodic_Load_4k_rough~26'
% JmagResultPath='F:\KDH\KDH\SCL_e10_WTPM_PatternD_R1_16kMap.jfiles\SC_e10_WirePeriodic~9\SC_e10_WirePeriodic_Load_16k_rough~27';
% JmagResultName='e10MS_ConductorModel_SCL_Load~13';
[~,JmagResultName,~]=fileparts(JmagResultPath);
JmagResultDIR=extractBefore(JmagResultPath,'.jfiles');
[JmagPJTDIR,JmagPJTName,~]=fileparts(JmagResultDIR);
JmagPJTPath=fullfile(JmagPJTDIR,[JmagPJTName,'.jproj']);
%% Get PartStruct


% need 2 open Jproj
app=callJmag
app.Show
app.Load(JmagPJTPath)
PartStruct=getJMAGDesignerPartStruct(app);
Lactive=150;
PartTable=struct2table(PartStruct);
BoolTargetSlot=contains(PartTable.Name,'Slot1/')|contains(PartTable.Name,'Slot2/');
WireTable=PartTable(BoolTargetSlot,:);
WireTable = sortrows(WireTable,'Name'); 
LayerNumber=4;
targetSlotNumber=2;
targetPartIndex=LayerNumber*targetSlotNumber;

savePartIDToMat(WireTable.partIndex, JmagPJTPath)

%% Get Wire Element and Node ID
for SlotIndex=1:height(WireTable)
    WireIndex=WireTable.partIndex(SlotIndex);
    [ElementId{SlotIndex}, NodeID{SlotIndex},NodeTable{SlotIndex},delaunyObj{SlotIndex}]...
    =getMeshData(app,WireIndex);
end

NodeID2Save=[];
for SlotIndex=1:height(WireTable)
        NodeID2Save=[NodeID2Save;NodeID{SlotIndex}];
end
saveNodeID2Mat(NodeID2Save, JmagPJTPath)

% As Var 2 Table
WireTable.NodeTable=NodeTable';
WireTable.NodeID=NodeID';
WireTable.ElementId=ElementId';
WireTable.DT=delaunyObj';



% Backup
refWireTableBackup=WireTable;
%% Load Mat File From JplotReader 
% -python
% DataStruct=load('ref_e10_WirePeriodic_Load_18k_rgh~32_Case28_MagB.mat')
if 38100==getPCRDPPortNumber
    matFileList=findMatFiles('D:\KangDH\Emlab_emach\tools\jmag\jplotReader');
else
    matFileList=findMatFiles('Z:\01_Codes_Projects\git_fork_emach\tools\jmag\jplotReader');
end
MagAmatFileList=matFileList(contains(matFileList,JmagResultName)&contains(matFileList,'MagB')&~contains(matFileList,'backup','IgnoreCase',true));
MagAmatFileList = sort(MagAmatFileList); 
[~,MatfileNames,~]=fileparts(MagAmatFileList);
% for caseIndex=1:len(MatfileNames)
%% temp
REFDTmatFileList=MagAmatFileList(contains(MagAmatFileList,'Case28'));
% REFDTmatFileList=REFDTmatFileList(~contains(REFDTmatFileList,'18k'));

% FqmatFileList=REFDTmatFileList(contains(REFDTmatFileList,'Fq'));
% MSmatFileList=REFDTmatFileList(contains(REFDTmatFileList,'MS'));
matFileList=REFDTmatFileList
DataStruct=load(REFDTmatFileList{1,1})
%5
parpool;  % 병렬 풀 시작 (필요한 경우)

% WireTable의 결과를 저장할 셀 배열 선언
WireTableResults = cell(1, 30);

parfor caseIndex = 1:30  % 'parfor'를 사용하여 병렬 처리
    % 초기화
    WireTable = [];
    
    % 데이터 로드
    % DataStruct = load(MagAmatFileList{caseIndex});
    
    %% Mapping 2 WireStruct > WireTable
    WireTable = mappingB2Slot(DataStruct, refWireTableBackup);  % WireTable 생성
    WireTable = sortrows(WireTable, "Name", "ascend");  % 정렬
    WireTable = cart2polPartTable(WireTable);  % 좌표 변환  
    WireTable=removevars(WireTable,'object')
    % 결과를 셀 배열에 저장
    WireTableResults{caseIndex} = WireTable;
end
delete(gcp('nocreate'));  % 병렬 풀 종료 (필요한 경우)

% 병렬 작업 완료 후 순차적으로 저장
for caseIndex = 1:30
    WireTable = WireTableResults{caseIndex};  % 병렬 결과 불러오기
    save([MatfileNames{caseIndex}, '_wireTable.mat'], 'WireTable');  % 저장
end

%% Scatter Plot
C = linspecer(481);
for slotIndex=1:height(WireTable)
    for timeIdx=52
    Btvalues = WireTable.TtimeTableByElerow{slotIndex}.(sprintf('Step%d', timeIdx)); 
    scatter3(WireTable.TtimeTableByElerow{slotIndex}.x,WireTable.TtimeTableByElerow{slotIndex}.y,abs(Btvalues),'MarkerFaceColor',C(4*timeIdx,:),'MarkerEdgeColor','none')
    hold on
    end
end
centerAllFigures
size(WireTable.DT{slotIndex}.Points(:,1))    % Node 
size(WireTable.TtimeTableByElerow{slotIndex}.x)  % ele
%% [TC] option 1
close all
ElementCenterX=WireTable.TtimeTableByElerow{slotIndex}.x;
ElementCenterY= WireTable.TtimeTableByElerow{slotIndex}.y;
ElementCenterValueArray=Btvalues;
DT=WireTable.DT{slotIndex};
% 원래 요소중심 데이터 Plot
scatter3(ElementCenterX,ElementCenterY,ElementCenterValueArray)
hold on
centerAllFigures
% 요소 중심에서의 x, y, z (Btvalues) 데이터
% 요소 중심에서의 x, y, z (Btvalues) 데이터
fitresult= fitElementCenterData(ElementCenterValueArray,ElementCenterX,ElementCenterY);
trSurf=plotMappedDelaunay(DT,fitresult);
centerAllFigures
