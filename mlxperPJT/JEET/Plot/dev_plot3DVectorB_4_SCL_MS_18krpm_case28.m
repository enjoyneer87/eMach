%% Table of Contents



%% Get PartStruct
    % need 2 open Jproj
app=callJmag
PartStruct=getJMAGDesignerPartStruct(app);
Lactive=150
idx=findMatchingIndexInStruct(PartStruct,'Name','Wire');
WireStruct=PartStruct(idx);

[~,index] = sortrows({WireStruct.Name}.'); 
WireStruct = WireStruct(index); 
clear index

LayerNumber=4
targetSlotNumber=8
targetPartIndex=LayerNumber*targetSlotNumber

%% Get Wire Element and Node ID
for SlotIndex=1:targetPartIndex
    WireIndex=WireStruct(SlotIndex).partIndex;
    [WireStruct(SlotIndex).ElementId, WireStruct(SlotIndex).NodeID,WireStruct(SlotIndex).NodeTable]...
    =getMeshData(app,WireIndex);
end

%% Trim Part Struct
WireStruct =WireStruct(1:targetPartIndex);

%% Load Mat File From JplotReader -python
% DataStruct=load('ref_e10_WirePeriodic_Load_18k_rgh~32_Case28_MagB.mat')
DataStruct=load('e10MS_ConductorModel_SCL_Load_240Step~21_Case1_MagB.mat')

%% Mapping 2 WireStruct > WireTable
WireStruct=mappingB2Slot(DataStruct,WireStruct)
WireTable=struct2table(WireStruct)
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




save('wireTable_SCL_MS_case1.mat',"WireTable")
%% Mesh Export
% MPToolCSVFilePath='D:/KangDH/Emlab_emach/mlxperPJT/JEET/From38100/REF_e10_WTPM_PatternD_TS_case28.csv'
MPToolCSVFilePath='D:/KangDH/Emlab_emach/mlxperPJT/JEET/From38100/MPtools/SCL_e10_WTPM_PatternD_MS_case28.csv'
% [model, pdeTriElements, pdeNodes, pdeQuadElements, quadElementsId, combinedElements,FieldDataSteps]= nastran2PDEMesh(MPToolCSVFilePath,'mm');
 [SCL_MSMesh,model,pdeTriElements,pdeNodes,pdeQuadElements]  = nastran2PDEMesh(MPToolCSVFilePath,'mm')
save('SCL_MS_18krpm_case28_Mesh.mat','SCL_MSMesh');
plotJMAGMesh(SCL_MSMesh)