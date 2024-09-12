% ref 
% Result4MDPICheckMotorCADExportToolTemp
parentPath='D:\KangDH\Thesis\e10\refModel'
[motFileList,~]=getResultMotMatList(parentPath);


%% try Final function 
filteredTable           =getMCADLabDataFromMotFile(motFileList{1});
originLabLinkTable      = reNameLabTable2LabLink(filteredTable);
MCADLinkTable           = originLabLinkTable;
plotMultipleInterpSatuMapSubplots(@plotFitResult, MCADLinkTable);


%% load JMAG response table
detectImportOptions("SCL_e10_WTPM_PatternD_R1_Load8kMap.csv","ReadVariableNames",true,"VariableNamesRow",1)
opts=detectImportOptions("SCL_e10_WTPM_PatternD_R1_Load8kMap.csv","VariableNamesLine",1)
preview("SCL_e10_WTPM_PatternD_R1_Load8kMap.csv",opts)

CSVList=findCSVFiles(pwd)'
CSVList=CSVList(contains(CSVList,'Map'))

for csvindex=1:len(CSVList)
    CSVList{csvindex,2}=readtable(CSVList{csvindex},opts);
    CSVList{csvindex,2}=removevars(CSVList{csvindex,2},'Var1');
end

%% Respons CaseTable 2 MCADLinkTable (dqTable) Format 
app=callJmag
CurStudyObj=app.GetCurrentStudy
CurStudyObj.GetName
sampleDTTable=getJMAGDesingTable(CurStudyObj)

MCADLinkvar=MCADLinkTable.Properties.VariableNames
DTvarName=sampleDTTable.Properties.VariableNames
IpkIndex=contains(DTvarName,'Ipk')
IrmsIndex=contains(DTvarName,'Irms')

PhIndex=contains(DTvarName,'MCADPhase')

IsIndex=contains(MCADLinkvar,'Is')
angIndex=contains(MCADLinkvar,'Angle')

DTvarName(IpkIndex)=MCADLinkvar(IsIndex)
DTvarName(PhIndex)=MCADLinkvar(angIndex)

sampleDTTable.Properties.VariableNames=DTvarName


JMAGLinkTable=[convertCharCell2Numeric(sampleDTTable(:,IrmsIndex).Variables),convertCharCell2Numeric(sampleDTTable(:,PhIndex).Variables)];
JMAGLinkTable=array2table(JMAGLinkTable,"VariableNames",[MCADLinkvar(IsIndex),MCADLinkvar(angIndex)]);
JMAGLinkTable.Is=JMAGLinkTable.Is*sqrt(2)

%% Make LabLinkTable 
JMAGLinkTable=addvars(JMAGLinkTable,zeros(height(JMAGLinkTable),1),'NewVariableNames','TotalACLoss');
for csvindex=1:len(CSVList)
    JMAGLinkTable.TotalACLoss=CSVList{csvindex,2}.Variables';

    CSVList{csvindex,3}=JMAGLinkTable;
end

for csvindex=1:len(CSVList)
plotMultipleInterpSatuMapSubplots(@plotFitResult, CSVList{csvindex,3});
hold on
end
%% 3D AC Loss Surface
n=[1 2 3]
mergeFigures(4.*(n-1)+1)
n=[4 5 6]
mergeFigures(4.*(n-1)+1)

%% Plot Per Speed
CSVListsTable=cell2table(CSVList);

CSVListsTable.Properties.VariableNames={'CSV','ResTable','dqTable'}

REFTable=CSVListsTable(1:3,:)
SpeedList=extractBetween(REFTable.CSV,'Load','kMap')
speed=convertCharCell2Numeric(SpeedList);
REFTable=addvars(REFTable,speed,'NewVariableNames','speedK')
REFTable=sortrows(REFTable,'speedK')

SCLTable=CSVListsTable(4:6,:)
SpeedList=extractBetween(SCLTable.CSV,'Load','kMap')
speed=convertCharCell2Numeric(SpeedList);
SCLTable=addvars(SCLTable,speed,'NewVariableNames','speedK')
SCLTable=sortrows(SCLTable,'speedK')


for SpeedIndex=1:3    
    [ACFitResult, tempGof, tempSingleDataSet] = createInterpDataSetofStrWithFieldName(REFTable.dqTable{SpeedIndex},'TotalACLoss');
    [id,iq]=pkgamma2dq(460,43.3);
    ACperspeed(SpeedIndex)=ACFitResult(id,iq);
end
scatter([8000,12000,18000],ACperspeed)

%% Export J Contour
CurStudyObj=app.GetCurrentStudy;
ModelObj =app.GetCurrentModel
ModelObj.RestoreCadLink
for caseIndex=1:30
    CurStudyObj.SetCurrentCase(caseIndex-1)
    app.View().SetView("SL_Slot5Slot6")
    app.View().SetStep(138)
    app.ExportImageWithSize(['D:/KangDH/Thesis/e10/JMAG/SCL18kc', num2str(1), 'J.png'], 640, 480)
end

CurStudyObj=app.GetCurrentStudy;
for caseIndex=1:30
    CurStudyObj.SetCurrentCase(caseIndex-1)
    app.View().SetView("Slot5Slot6View")
    app.View().SetStep(138)
    app.ExportImageWithSize(['D:/KangDH/Thesis/e10/JMAG/REF18kc', num2str(caseIndex), 'J.png'], 8000, 6000)
end
%% export Slot J
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
for Index=1:length(WireStruct)
    WireIndex=WireStruct(Index).partIndex;
    [WireStruct(Index).ElementId, WireStruct(Index).NodeID]=devgetMeshData(app,WireIndex);
end
% Babs/Brad/Bt - per time
    % Ref/SC - 동일하니 하나만  - SC가 mesh가 촘촘

%%1) Manual CSV 
% exportData=exportAirGapBField(i_Stator_OD,app)
PartIdList=[WireStruct.partIndex];
exportFilePath=exportFieldData2CSV(app,'Jloss','JEET',PartIdList,'ref','_Load_18k_rgh');

%% Read B Table
exportFilePath=findCSVFiles(pwd)
LoadexportFilePath=exportFilePath(contains(exportFilePath,'_Load_18k_rgh','IgnoreCase',true));
for CaseIndex=2:length(LoadexportFilePath)
    filePath=LoadexportFilePath{CaseIndex};
    [FieldData{CaseIndex},rawTable]=readJMAGFieldTable(filePath);
end
MatFilePath=strrep(LoadexportFilePath{2},'.csv','Table.mat')
save(MatFilePath,'FieldData')

load(MatFilePath)
%% 3D Jplot
stepSC=4
stepList=stepSC*[1,44,86,120]
PosTable=FieldData.positionTable; 
rawTable=FieldData.rawTable
% figure(1) % Abs

for stepIndex=1:length(stepList)
        stepData=stepList(stepIndex);
        ValueVecPerNode=rawTable(:,stepData).Variables;
        xPos2Plot=PosTable.("Position X");
        yPos2Plot=PosTable.("Position Y");
        % Value2Plot=WattmCubic2wmmCubic(ValueVecPerNode(:));
        Value2Plot=ValueVecPerNode(:)/1000;

        if stepData==1*stepSC
        stem3(xPos2Plot,yPos2Plot,Value2Plot,'O:','DisplayName',['step',num2str(stepData)],'LineWidth',2)
        % stem(yPos2Plot,Value2Plot,'O:','DisplayName',['step',num2str(stepData)],'LineWidth',2)
        elseif stepData==44*stepSC
        stem3(xPos2Plot,yPos2Plot,Value2Plot,'x--','DisplayName',['step',num2str(stepData)],'LineWidth',2);
        % stem(yPos2Plot,Value2Plot,'x--','DisplayName',['step',num2str(stepData)],'LineWidth',2);
        elseif stepData==88*stepSC
        stem3(xPos2Plot,yPos2Plot,Value2Plot,'Diamond:','DisplayName',['step',num2str(stepData)],'LineWidth',2);
        % stem(yPos2Plot,Value2Plot,'Diamond:','DisplayName',['step',num2str(stepData)],'LineWidth',2);
        elseif stepData==120*stepSC
        stem3(xPos2Plot,yPos2Plot,Value2Plot,'^:','DisplayName',['step',num2str(stepData)],'LineWidth',2);
        % stem(yPos2Plot,Value2Plot,'^:','DisplayName',['step',num2str(stepData)],'LineWidth',2);
        end
        hold on
end
[axisState,viewState,DataAspectRatio]=lockAxisAndView()

%% plot Mesh

MPToolCSVFilePath='JEET_ref_e10_WirePeriodic_Load_18k_rgh_case1_J_MPtools.csv'
% [model,pdeTriElements,pdeNodes,pdeQuadElements]  = nastran2PDEMesh(MPToolCSVFilePath,'mm');
pdeMeshMatPath=strrep('e10_JMAGWireTemplate90deg.dxf','.dxf','.mat')
% quadMeshPath=[extractBefore(pdeMeshMatPath,'.mat'),'quad.mat']
% save(pdeMeshMatPath,"model")
% save(quadMeshPath,"pdeQuadElements")

load(pdeMeshMatPath)
load(quadMeshPath)
MeshPlot=pdeplot(model.Mesh.Nodes,model.Mesh.Elements)
MeshPlot.Color=[0.80,0.80,0.80];  % grey

hold on
x = pdeNodes(1,:);
y = pdeNodes(2,:);
quadmesh(pdeQuadElements, x, y);
DXFPath="D:\KangDH\Emlab_emach\mlxperPJT\JEET\From38100/e10_JMAGWireTemplate90deg.dxf";
DXFtool(DXFPath)
ax=gca
restoreView(ax,axisState,viewState,DataAspectRatio)

% saveFigures2eps(pwd)
% export_fig 사용
addpath('export_fig');  % export_fig 폴더로 경로를 설정

% 렌더러를 painters로 설정 후 export_fig로 EPS 저장
% set(gcf, 'Renderer', 'painters');
% export_fig('my_plot.eps', '-depsc');
formatterFigure4Paper('double','2x2')
exportgraphics(gcf,'JlossImage.pdf','ContentType','image')
legend hide

obj3d=findall(gcf,'Type','Stem');
obj3d=findall(gcf,'Type','line');

% obj3d(1)
for chIndex=1:len(obj3d)
    % exportgraphics(gcf,'test.pdf','ContentType','vector')
set(obj3d(chIndex), 'XData', [], 'YData', [],'ZData',[]);
end
legend
trimLegendToIndex(3)
setlegendBoxShape(3)
exportgraphics(gcf,'JlossLegned.pdf','ContentType','vector')

savefig(gcf,'test.fig')
% dev_plot3DVectorB
%% 2D
figure(2)

[thetaPosAll,RPosAll]=cart2pol(FieldData{caseIndex}.positionTable.("Position X"),FieldData{caseIndex}.positionTable.("Position Y"))
MaxThetaIndex=find(difftol(thetaPosAll,max(thetaPosAll),1e-2)&difftol(RPosAll,min(RPosAll),1e-2));
MinThetaIndex=find(difftol(thetaPosAll,min(thetaPosAll),1e-2)&difftol(RPosAll,min(RPosAll),1e-2));

plot([0:3:360],rawTable(1,361:481).Variables)

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

%% MQS

