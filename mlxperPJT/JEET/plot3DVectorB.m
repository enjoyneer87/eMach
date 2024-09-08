%% Mesh 3D 



%% MS 
app=callJmag
MotFilePath='Z:\Simulation\JEETACLossValid_e10_v24\refModel\e10_UserRemesh.mot'
refMSjprojPath='Z:/Simulation/JEETACLossValid_e10_v24/refModel/e10_v24.jfiles';

[refMSjprojPath] = checkMotNJprojLink(MotFilePath,refMSjprojPath,app);
jprojFiles=app.GetProjectFolderPath;

if ~strcmp(jprojFiles,refMSjprojPath)
    app.Load(refMSjprojPath)
end
Model=app.GetCurrentModel;
Model.RestoreCadLink
geomApp=app.CreateGeometryEditor(0);
WireTemplateObj=getWireTemplateObject(geomApp);

if WireTemplateObj.IsValid
    isConductor=2; % wireTemplate
else
    isConductor=0;
end
%% MS Slot B Vector - on 3D Plane
%% Model PartName Change & Model Set - PartStruct
if isConductor==0
    ConductorModelObj=Model;
end
PartStruct          =getJMAGDesignerPartStruct(app);
PartStruct=getEdgeVertexIdwithXYZCheck(PartStruct,app);   
PartStructByType    =convertJmagPartStructByType(PartStruct);
changeJMAGPartNameTable(PartStructByType.StatorCoreTable,app)


i_Stator_OD=2*max([PartStruct.VertexMaxRPos]);
PartStruct          =getJMAGDesignerPartStruct(app);
idx=findMatchingIndexInStruct(PartStruct,'Name','Stator');
WireStruct=PartStruct(idx);
idx=contains({WireStruct.Name},'StatorCore',IgnoreCase=true);
WireStruct=WireStruct(~idx);

length(WireStruct)
%% Get Wire Element and Node ID
for Index=1:length(WireStruct)
    WireIndex=WireStruct(Index).partIndex;
    [WireStruct(Index).ElementId, WireStruct(Index).NodeID]=devgetMeshData(app,WireIndex);
end


% Babs/Brad/Bt - per time
    % Ref/SC - 동일하니 하나만  - SC가 mesh가 촘촘

%%1) Manual CSV 
% exportData=exportAirGapBField(i_Stator_OD,app)
PartIdList=[WireStruct.partIndex];
exportFilePath=exportFieldData2CSV(app,'B','JEET',PartIdList,'ref','_Load');
%2) MPT tool >CSV /3) Manual CSV > MPT tool로 결국 Mesh 추출필요
%3) jquery말고 API JplotReader 이름 뭐였더라 아 c++사용필요 
% Z:\01_Codes_Projects\git_fork_emach\mlxperPJT\JEET\devSettingJPlotReader.m
% No AirRegion > EMdyne문의

%% Mesh 플로팅
% figure;

% MPToolCSVFilePath='Z:/Simulation/JEETACLossValid_e10_v24/refModel/ExportMPtools/MSField.csv';
MPToolCSVFilePath='Z:/Simulation/JEETACLossValid_e10_v24/refModel/ExportMPtools/MSField_Fillet.csv'
[model,pdeTriElements,pdeNodes,pdeQuadElements]  = nastran2PDEMesh(MPToolCSVFilePath);


%% Read B Table
LoadexportFilePath=exportFilePath(contains(exportFilePath,'_Load','IgnoreCase',true));
for CaseIndex=1:length(LoadexportFilePath)
    filePath=LoadexportFilePath{CaseIndex};
    FieldData{CaseIndex}=readJMAGFieldTable(filePath);
end


StepList=FieldData{1}.AbsTable.Properties.VariableNames;
view(3)
%% Abs Table/XTable/YTable
dev_plot3DVectorB
figure(2)

[thetaPosAll,RPosAll]=cart2pol(FieldData{caseIndex}.positionTable.("Position X"),FieldData{caseIndex}.positionTable.("Position Y"))
MaxThetaIndex=find(difftol(thetaPosAll,max(thetaPosAll),1e-2)&difftol(RPosAll,min(RPosAll),1e-2));
MinThetaIndex=find(difftol(thetaPosAll,min(thetaPosAll),1e-2)&difftol(RPosAll,min(RPosAll),1e-2));


plot([0:3:360],FieldData{caseIndex}.AbsTable(MaxThetaIndex,:).Variables,'*--','DisplayName','Left')
hold on
plot([0:3:360],FieldData{caseIndex}.AbsTable(MinThetaIndex,:).Variables,'^-','DisplayName','Right')
formatterFigure4Paper('double','2x2')
ax=gca
ax.XLim=[0 360]
ax.XLabel.String='Electrical Angle[deg]'
ax.YLabel.String='B_{abs}[T]'

% pdegploaxt(model)
close all
%% MS Core M Vector - on 3D Plane 
% JplotReaderData - NO Air Region
outputMatPath='Z:\01_Codes_Projects\git_Pyleecan_fork\output_data.mat'
JplotReaderData=load(outputMatPath)

scatter3(BData.element_centers(:,4),BData.element_centers(:,5),BData.component_data(:,2),'r')
hold on
scatter3(BData.element_centers(:,4),BData.element_centers(:,5),BData.component_data(:,3),'k')
hold on

%% MQS

