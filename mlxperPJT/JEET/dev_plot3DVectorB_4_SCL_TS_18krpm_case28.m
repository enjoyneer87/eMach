%% Table of Contents



%% Get PartStruct
    % need 2 open Jproj
app=callJmag
PartStruct=getJMAGDesignerPartStruct(app);
Lactive=150

PartTable=struct2table(PartStruct);

BoolTargetSlot=contains(PartTable.Name,'Slot1/')|contains(PartTable.Name,'Slot2/')...
    |contains(PartTable.Name,'Slot8/')|contains(PartTable.Name,'Slot7/');
Slot1=findMatchingIndexInStruct(PartStruct,'Name','Slot1/');
Slot2=findMatchingIndexInStruct(PartStruct,'Name','Slot2');
Slot7=findMatchingIndexInStruct(PartStruct,'Name','Slot7');
Slot8=findMatchingIndexInStruct(PartStruct,'Name','Slot8');

WireTable=PartTable(BoolTargetSlot,:);
WireTable = sortrows(WireTable,'Name'); 
LayerNumber=4
targetSlotNumber=8
targetPartIndex=LayerNumber*targetSlotNumber

%% Get Wire Element and Node ID
for SlotIndex=1:height(WireTable)
    WireIndex=WireTable.partIndex(SlotIndex);
    [ElementId{SlotIndex}, NodeID{SlotIndex},NodeTable{SlotIndex}]...
    =getMeshData(app,WireIndex);
end

ElementId=ElementId'
NodeID=NodeID'
NodeTable=NodeTable'
%% As Var
WireTable.NodeTable=NodeTable;
WireTable.NodeID=NodeID;
WireTable.ElementId=ElementId;
%% Load Mat File From JplotReader -python
% DataStruct=load('ref_e10_WirePeriodic_Load_18k_rgh~32_Case28_MagB.mat')
DataStruct=load('SC_e10_WirePeriodic_Load_18k_rough240steps~28_Case1_MagB.mat')

%% Mapping 2 WireStruct > WireTable
WireTable=mappingB2Slot(DataStruct,WireTable)
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


save('wireTable_SCL_TS_18krpm_case28.mat',"WireTable")

%% Mesh Export
% MPToolCSVFilePath='D:/KangDH/Emlab_emach/mlxperPJT/JEET/From38100/REF_e10_WTPM_PatternD_TS_case28.csv'
MPToolCSVFilePath='D:/KangDH/Emlab_emach/mlxperPJT/JEET/From38100/MPtools_SCL_e10_WTPM_PatternD_TS_case28.csv'
% [model, pdeTriElements, pdeNodes, pdeQuadElements, quadElementsId, combinedElements,FieldDataSteps]= nastran2PDEMesh(MPToolCSVFilePath,'mm');
 [SCL_TSMesh,model,pdeTriElements,pdeNodes,pdeQuadElements]  = nastran2PDEMesh(MPToolCSVFilePath,'mm')
save('SCL_TS_18krpm_case28_Mesh.mat','SCL_TSMesh');
