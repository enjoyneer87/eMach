

% ref 
% Result4MDPICheckMotorCADExportToolTemp
JMAGParentPath='D:\KangDH\Thesis\e10';
parentPath='F:\KDH\Thesis\JEET'
[motFileList,~]=getResultMotMatList(parentPath);
%% Plot AC Loss Map
% try Final function

filteredTable           =getMCADLabDataFromMotFile(motFileList{1});
originLabLinkTable      = reNameLabTable2LabLink(filteredTable);
MCADLinkTable           = originLabLinkTable;
plotMultipleInterpSatuMapSubplots(@plotFitResult, MCADLinkTable);
close all
% [TC]make Response Table


JPJTList=findJPJTFiles(JMAGParentPath)'
R1List=JPJTList(contains(JPJTList,'R1'))
R1PatternDList=R1List(contains(R1List,'PatternD'))
R1PatternDList=R1PatternDList(~contains(R1PatternDList,'4k'))

for projectIndex=1:len(R1PatternDList)
    app.load(R1PatternDList{projectIndex})
    curStudyObj=app.GetCurrentStudy
    csvPath=mkJMAGResponseTable(app,curStudyObj,'joule',BoolAllCases,'Total')
end
% load JMAG response table

detectImportOptions("SCL_e10_WTPM_PatternD_R1_Load8kMap.csv","ReadVariableNames",true,"VariableNamesRow",1)
opts=detectImportOptions("SCL_e10_WTPM_PatternD_R1_Load8kMap.csv","VariableNamesLine",1)
preview("SCL_e10_WTPM_PatternD_R1_Load8kMap.csv",opts)

CSVList=findCSVFiles(pwd)'
% List4k=findCSVFiles(pwd)'
% List4k=List4k(contains(List4k,'4k'))
% List4k=List4k(contains(List4k,'case','IgnoreCase',true))

CSVList=CSVList(contains(CSVList,'Map'))
% CSVList=[CSVList;List4k]
for csvindex=1:len(CSVList)
    CSVList{csvindex,2}=readtable(CSVList{csvindex},opts);
    CSVList{csvindex,2}=removevars(CSVList{csvindex,2},'Var1');
end
% Respons CaseTable 2 MCADLinkTable (dqTable) Format

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
% Make LabLinkTable

JMAGLinkTable=addvars(JMAGLinkTable,zeros(height(JMAGLinkTable),1),'NewVariableNames','TotalACLoss');
for csvindex=1:len(CSVList)
    JMAGLinkTable.TotalACLoss=CSVList{csvindex,2}.Variables'/1000;

    CSVList{csvindex,3}=JMAGLinkTable;
end

% make plot List

% def Speed
CSVListsTable=cell2table(CSVList);
CSVListsTable.Properties.VariableNames={'CSV','ResTable','dqTable'}
REFTable=CSVListsTable(1:4,:)
SpeedList=extractBetween(REFTable.CSV,'Load','kMap')
speed=convertCharCell2Numeric(SpeedList);
REFTable=addvars(REFTable,speed,'NewVariableNames','speedK')
REFTable=sortrows(REFTable,'speedK')
SCLTable=CSVListsTable(5:8,:)
SpeedList=extractBetween(SCLTable.CSV,'Load','kMap')
speed=convertCharCell2Numeric(SpeedList);
SCLTable=addvars(SCLTable,speed,'NewVariableNames','speedK')
SCLTable=sortrows(SCLTable,'speedK')
%

save('SCLTableMapPerSpeed.mat','SCLTable')
save('REFTableMapPerSpeed.mat','REFTable')

% Fig1. Plot Total AC Loss Dq Map

load('SCLTableMapPerSpeed.mat');
load('REFTableMapPerSpeed.mat');
CSVList=[REFTable;SCLTable]
CSVList=table2cell(CSVList)
close all
for csvindex=1:height(REFTable)
plotMultipleInterpSatuMapSubplots(@plotFitResult,REFTable.dqTable{csvindex});
n=csvindex;
close(n+1:n+3)
end


for csvindex=1:height(SCLTable)
plotMultipleInterpSatuMapSubplots(@plotFitResult,SCLTable.dqTable{csvindex});
n=csvindex;
close(n+5:n+7)
hold on
end

%% update Marker and displayname
colorList={'k','r','b','g'}
markerList={'o','^'}
group = ceil((1:len(CSVList)) / (len(CSVList)/2)); % 3개씩 그룹으로 할당
for csvindex=1:len(CSVList)
    cf=figure(csvindex)
    divided =csvindex
    divisor =len(CSVList)/2
    ax=cf.Children;
    remainder=mod(divided,divisor);
    ModelIndex=group(csvindex);
    if remainder==0
    remainder=divisor;
    end
    legend([num2str(SCLTable.speedK(remainder)),'k','[RPM]'])
    % 모든 figure 객체 중에서 Marker 속성이 있는 객체를 찾음
    markerObjects = findobj(ax, '-property', 'Marker');
    % Marker 속성이 비어있지 않은 객체만 필터링
    markerObjects         = markerObjects(~cellfun(@isempty, get(markerObjects, 'Marker')));
    markerObjects(1).Marker=markerList{ModelIndex}
    markerObjects(1).MarkerFaceColor=colorList{remainder};
    markerObjects(1).MarkerSize=12
    markerObjects(1).MarkerEdgeColor=colorList{remainder};
end

%% merge Figure By Speed N Model
startNList=[1,len(CSVList)/2+1]
for nIndex=1:len(startNList)
    n=startNList(nIndex)
    figlist=[n:n+3];
    if n==1
        for figN=1:len(figlist)
        mergeFigures([figlist(figN) len(CSVList)/2+figlist(figN)]) % 속도별로 합치기
        % 모든 figure 객체 중에서 Marker 속성이 있는 객체를 찾음
        markerObjects = findobj(gcf, 'Type', 'line');
            for markerIndex=1:len(markerObjects)          
                if contains(markerObjects(markerIndex).Marker,markerList{1})
                    markerObjects(markerIndex).DisplayName='REF'
                elseif strcmp(markerObjects(markerIndex).Marker,markerList{2})
                    markerObjects(markerIndex).DisplayName='SCL'
                end
            end
        end
    end
    mergeFigures(figlist)   % 모델별로 합치기
end
%% update per Speed 
for figIndex=len(CSVList)+1:len(CSVList)+len(CSVList)/2
    gcf=figure(figIndex)
    markerObjects = findobj(gcf, 'Type', 'Axes');
    markerObjects.ZLabel.String='P[kW]'
    markerObjects.XLabel.String='I_{d,pk}[A]'
    markerObjects.YLabel.String='I_{q,pk}[A]'
    legend
    lineobj=findobj(markerObjects,'Type','line')
    setlegendBoxShape(len(lineobj))
    formatterFigure4Paper('double','2x2')
    grid on
end
%% upated Per Model
for figIndex=len(CSVList)+len(CSVList)/2+1:len(CSVList)+len(CSVList)/2+2
    gcf=figure(figIndex)
    markerObjects = findobj(gcf, 'Type', 'Axes');
    markerObjects.ZLabel.String='P[kW]'
    markerObjects.XLabel.String='I_{d,pk}[A]'
    markerObjects.YLabel.String='I_{q,pk}[A]'
    legend
    lineobj=findobj(markerObjects,'Type','line')
    setlegendBoxShape(len(lineobj))
    formatterFigure4Paper('double','2x2')
    grid on
end

% Temporal Save 2 Fig File

close([1:len(CSVList)]);
speed=REFTable.speedK;
gcf=figure(len(CSVList)+len(CSVList)/2+1)
markerObjects = findobj(gcf, 'Type', 'Axes');
markerObjects.ZLim=[0 30]
speedList=sort(speed,'ascend');
for figIndex=len(CSVList)+1:len(CSVList)+len(CSVList)/2
    speedNum=figIndex-len(CSVList);
    curRPM=speedList(speedNum)
    savefig(figure(figIndex),['TSFEA_ACFitSurf_',num2str(curRPM),'rpm'])
end

for figIndex=len(CSVList)+len(CSVList)/2+1:len(CSVList)+len(CSVList)/2+2
    speedNum=figIndex-len(CSVList)-1
    if speedNum>len(CSVList)/2
        ModelName='REF'
    else
        ModelName='SCL'
    end
    grid on
    savefig(figure(figIndex),[ModelName,'_TSFEA_TotalACFitSurfPerSpeed'])
end

% Export

% 렌더러를 painters로 설정 후 export_fig로 EPS 저장
% set(gcf, 'Renderer', 'painters');
% export_fig('my_plot.eps', '-depsc');
for figIndex=len(CSVList)+1:len(CSVList)+len(CSVList)/2
    speedNum=figIndex-len(CSVList);
    curRPM=speedList(speedNum)
    % legend hide
    % % image
    pdfPath=['TSFEA_ACFitSurf_',num2str(curRPM),'rpm.pdf'];
    exportgraphics(figure(figIndex),pdfPath,'ContentType','image')
    % vector
    objline=findall(figure(figIndex),'Type','line');
    obj3d=findall(figure(figIndex),'Type','Surface');
    for chIndex=1:len(obj3d)
    set(obj3d(chIndex), 'XData', [], 'YData', [],'ZData',[]);
    end
    for chIndex=1:len(objline)
    set(objline(chIndex), 'XData', [], 'YData', [],'ZData',[]);
    end
    legend Show
    setlegendBoxShape(2)
    pdfPath=['TSFEA_ACFitSurf_',num2str(curRPM),'rpmLenged.pdf'];
    exportgraphics(figure(figIndex),pdfPath,'ContentType','vector')
end
%% Per Model
% for figIndex=len(CSVList)+len(CSVList)/2+1:len(CSVList)+len(CSVList)/2+2
for figIndex=len(CSVList)+len(CSVList)/2+1:len(CSVList)+len(CSVList)/2+2
    speedNum=figIndex-len(CSVList)-1
    if speedNum>len(CSVList)/2
        ModelName='REF'
    else
        ModelName='SCL'
    end
    % image
    % legend hide
    PDFdName=[ModelName,'_TSFEA_TotalACFitSurfPerSpeed.pdf']
    exportgraphics(figure(figIndex),PDFdName,'ContentType','image')
    % Vector
    objline=findall(figure(figIndex),'Type','line');
    obj3d=findall(figure(figIndex),'Type','Surface');
    for chIndex=1:len(obj3d)
    set(obj3d(chIndex), 'XData', [], 'YData', [],'ZData',[]);
    end
    for chIndex=1:len(objline)
    set(objline(chIndex), 'XData', [], 'YData', [],'ZData',[]);
    end
    legend Show
    setlegendBoxShape(2)
    PDFlegendName=[ModelName,'_TSFEA_TotalACFitSurfPerSpeedLegend.pdf']
    exportgraphics(figure(figIndex),PDFlegendName,'ContentType','vector')
end

% Fig 2. Plot Per Speed

TableList={REFTable,SCLTable}

for ModelIndex=1:2
    ModelTable=TableList{ModelIndex}
    [~,csvName,~]=fileparts(ModelTable{1,1})
    ModelName=strsplit(csvName{1},'_')
    for SpeedIndex=1:4 
        [ACFitResult, tempGof, tempSingleDataSet] = createInterpDataSetofStrWithFieldName(ModelTable.dqTable{SpeedIndex},'TotalACLoss');
        [id,iq]=pkgamma2dq(sqrt(2)*460,43.3);
        ACperspeed(SpeedIndex)=ACFitResult(id,iq);
    end
    plot([speedList]',ACperspeed,'Marker',markerList{ModelIndex},'DisplayName',ModelName{1});
    hold on
end
% clear gcf
grid on
markerObjects = findobj(gcf, 'Type', 'Axes');
markerObjects.YLabel.String='AC Loss[kW]'
markerObjects.XLabel.String='Speed[kRPM]'
formatterFigure4Paper('double','2x2')
savefig(gcf,['Comp_TotalMaxIpkPerSpeed']);

%% Plot J Contour 
% Fig 3.Export J Contour

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
%% Fig. Slot JLoss 3D
% export Slot J 3D

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
%%
exportFilePath=findCSVFiles(pwd)
LoadexportFilePath=exportFilePath(contains(exportFilePath,'_Load_18k_rgh','IgnoreCase',true));
for CaseIndex=2:length(LoadexportFilePath)
    filePath=LoadexportFilePath{CaseIndex};
    [FieldData{CaseIndex},rawTable]=readJMAGFieldTable(filePath);
end
MatFilePath=strrep(LoadexportFilePath{2},'.csv','Table.mat')
save(MatFilePath,'FieldData')
load(MatFilePath)
% Fig 4. 3D Jplot

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
% plot Mesh

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
% 

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


%%