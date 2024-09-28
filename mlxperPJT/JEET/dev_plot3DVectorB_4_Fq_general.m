%% Table of Contents
% def Path
% Get PartStruct
% Get Wire Element and Node ID
% Load Mat File From JplotReader  need Do prior -with python Code
%%
% JmagResultName='e10MS_ConductorModel_REF_Load~16_';
JmagResultPath='D:\KangDH\Thesis\e10\JMAG\SCL_e10_WTPM_PatternD_R1_FqMap_MSFp.jfiles\SC_e10_WirePeriodic~9\SC_e10_WirePeriodic_Load_FqWithShiftAvgDiffMu~33';
[~,JmagResultName,~]=fileparts(JmagResultPath)
% JmagResultName='e10MS_ConductorModel_SCL_Load~13';
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
    [ElementId{SlotIndex}, NodeID{SlotIndex},NodeTable{SlotIndex}]...
    =getMeshData(app,WireIndex);
end
% As Var 2 Table
WireTable.NodeTable=NodeTable';
WireTable.NodeID=NodeID';
WireTable.ElementId=ElementId';
% Backup
refWireTableBackup=WireTable;
%% Load Mat File From JplotReader -python
% DataStruct=load('ref_e10_WirePeriodic_Load_18k_rgh~32_Case28_MagB.mat')
matFileList=findMatFiles('D:\KangDH\Emlab_emach\tools\jmag\jplotReader')
MagBmatFileList=matFileList(contains(matFileList,JmagResultName)&contains(matFileList,'MagB'))'
MagBmatFileList = sort(MagBmatFileList); 
[~,MatfileNames,~]=fileparts(MagBmatFileList)

for caseIndex=1:len(MatfileNames)
    WireTable=[];
    DataStruct=load(MagBmatFileList{caseIndex});
    %% Mapping 2 WireStruct > WireTable
    WireTable=mappingB2Slot(DataStruct,refWireTableBackup);
    WireTable=sortrows(WireTable,"Name","ascend");
    %% cart2 pol
    %[tb unit allocate]
    if isempty(WireTable.elementCentersTable{1}.Properties.VariableUnits)
        disp('단위 확인필요합니다 일단은 mm로 할당합니다')
        WireTable.elementCentersTable{1}.Properties.VariableUnits={'id','partId','eleType','mm','mm','mm','mm^2'}
        for slotIndex=1:height(WireTable)
                WireTable(slotIndex,:).elementCentersTable{:}.x=m2mm(WireTable(slotIndex,:).elementCentersTable{:}.x)
                WireTable(slotIndex,:).elementCentersTable{:}.y=m2mm(WireTable(slotIndex,:).elementCentersTable{:}.y)
        end
    else
        if ~any(contains(WireTable.elementCentersTable{1}.Properties.VariableUnits,'mm'))
            for slotIndex=1:height(WireTable)
                WireTable(slotIndex,:).elementCentersTable{:}.x=m2mm(WireTable(slotIndex,:).elementCentersTable{:}.x)
                WireTable(slotIndex,:).elementCentersTable{:}.y=m2mm(WireTable(slotIndex,:).elementCentersTable{:}.y)
            end
        end
    end
    WireTable=cart2polPartTable(WireTable);
    save([MatfileNames{caseIndex},'_wireTable.mat'],"WireTable")
end

%% Mesh Export
% MPToolCSVFilePath='D:/KangDH/Emlab_emach/mlxperPJT/JEET/From38100/REF_e10_WTPM_PatternD_TS_case28.csv'
MPToolCSVFilePath='D:/KangDH/Emlab_emach/mlxperPJT/JEET/From38100/MPtools_SCL_e10_WTPM_PatternD_TS_case28.csv'
% [model, pdeTriElements, pdeNodes, pdeQuadElements, quadElementsId, combinedElements,FieldDataSteps]= nastran2PDEMesh(MPToolCSVFilePath,'mm');
 % [SCL_TSMesh,model,pdeTriElements,pdeNodes,pdeQuadElements]  = nastran2PDEMesh(MPToolCSVFilePath,'mm')
% save('SCL_TS_18krpm_case28_Mesh.mat','SCL_TSMesh');

% devSurfInterp4HYBMS
% devmkBSFDTable
