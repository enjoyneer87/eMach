%% Get PartStruct
app=callJmag
PartStruct=getJMAGDesignerPartStruct(app);
Lactive=150
idx=findMatchingIndexInStruct(PartStruct,'Name','Wire');
WireStruct=PartStruct(idx);
[~,index] = sortrows({WireStruct.Name}.'); 
WireStruct = WireStruct(index); 
clear index
LayerNumber=4
targetSlotNumber=1
targetPartIndex=LayerNumber*targetSlotNumber
%% 이걸 JplotTable에서 part ID별로 땡기는걸로 수정한다음 partStruct와 매칭
%% Get Wire Element and Node ID
for SlotIndex=1:4
    WireIndex=WireStruct(SlotIndex).partIndex;
    [WireStruct(SlotIndex).ElementId, WireStruct(SlotIndex).NodeID,WireStruct(SlotIndex).NodeTable]...
    =getMeshData(app,WireIndex);
end

%% Trim Part Struct
WireStruct =WireStruct(1:targetPartIndex);
%% Load Mat File From JplotReader -python
% DataStruct=load('e10MS_ConductorModel_REF_Load~16_Case28_MagB.mat')
DataStruct=load('e10MS_ConductorModel_REF_Load_240Step~20_Case1_MagB.mat')

%% Mapping 2 WireStruct > WireTable
WireStruct=mappingB2Slot(DataStruct,WireStruct)
WireTable=struct2table(WireStruct)
WireTable=sortrows(WireTable,"Name","ascend");
save('wireTable_REF_MS_Step240_case28.mat',"WireTable")



%% Back up
% SlotList=[ones(1,4), 4*ones(1,4), 100*ones(1,4),120*ones(1,4),230*ones(1,4),236*ones(1,4)]
% 
% DataStruct=load('ref_e10_WirePeriodic_Load_18k_rgh~32_Case28_MagB.mat')
% MPToolCSVFilePath='JEET_ref_e10_WirePeriodic_Load_18k_rgh_case1_J_MPtools.csv'
[model,pdeTriElements,pdeNodes,pdeQuadElements]  = nastran2PDEMesh(MPToolCSVFilePath,'mm');

stepdata = extractJMAGFieldVectorFromMPtoolCSV(MPToolCSVFilePath,16001)
WireStruct=mappingB2Slot(DataStruct,WireStruct)

close all

timeList=(241:40:481)
SlotList={'x','o','^','v','.','diamond','x','o','^','v','.','diamond','x','o','^','v','.','diamond','x','o','^','v','.','diamond'}
ColorList=colormap("jet");
timeColorList=ColorList(1:256/len(timeList):256,:);
timeColorList=num2cell(timeColorList,2);
%%
WireTable=struct2table(WireStruct)
WireTable=sortrows(WireTable,"Name","ascend");
% for slotIndex=1:len(PartStruct)

size(WireTable.elementCentersTable{1})
size(WireTable.fieldxTimeTable{1})
% save('wireTable_REF_MS_case28.mat',"WireTable")
load('wireTable_REF_MS_case28.mat')
save('wireTable_REF_TS_case28.mat',"WireTable")
close all

figure(1)
for slotIndex=1:4
    for timeindex=1:len(timeList)
        BData=WireTable(slotIndex,:);
        scatter3(m2mm(BData.elementCentersTable{:}(:,'x').Variables),m2mm(BData.elementCentersTable{:}(:,'y').Variables),BData.fieldxTimeTable{:}(timeList(timeindex),:).Variables,'MarkerEdgeColor',timeColorList{timeindex},'MarkerFaceColor','none','Marker',SlotList{slotIndex},'DisplayName',num2str(3*timeList(timeindex)-3))
        hold on
    end
end
[axisState,viewState,DataAspectRatio]=lockAxisAndView
MeshPlot=pdeplot(model.Mesh.Nodes,model.Mesh.Elements)
MeshPlot.Color=[0.80,0.80,0.80];  % grey
hold on
x = pdeNodes(1,:);
y = pdeNodes(2,:);
quadmesh(pdeQuadElements, x, y);
ax=gca
restoreView(ax, axisState, viewState,DataAspectRatio)
centerAllFigures
triplot(DT)
hold on
line_handles = findobj(gca, 'Type','line');
set(line_handles, 'Color', [0.8,0.8,0.8]); % 예: 검은색
% savefig(figure(1),'e10MS_ConductorModel_REF_Load_Case28_MagBx')
figure(2)

% for slotIndex=1:len(PartStruct)
for slotIndex=1:1
    for timeindex=1:len(timeList)
        BData=WireTable(slotIndex,:);
        scatter3(m2mm(BData.elementCentersTable{:}(:,'x').Variables),m2mm(BData.elementCentersTable{:}(:,'y').Variables),BData.fieldyTimeTable{:}(timeList(timeindex),:).Variables,'MarkerEdgeColor',timeColorList{timeindex},'MarkerFaceColor','none','Marker',SlotList{slotIndex},'DisplayName',num2str(3*timeList(timeindex)-3))
        hold on
    end
end
lockAxisAndView
triplot(DT)
hold on
line_handles = findobj(gca, 'Type','line');
set(line_handles, 'Color', [0.8,0.8,0.8]); % 예: 검은색
% savefig(figure(2),'e10MS_ConductorModel_REF_Load_Case28_MagBy')


DXFPath="D:\KangDH\Emlab_emach\mlxperPJT\JEET\From38100/e10_JMAGWireTemplate90deg.dxf";
hold on
% DXFtool(DXFPath)
% ax=gca
% ax.DataAspectRatio=[1 1 0.05]
% ax.XLim=[60 100]
% ax.YLim=[0 70]
% %
% % formatterFigure4Paper('double','2x2')