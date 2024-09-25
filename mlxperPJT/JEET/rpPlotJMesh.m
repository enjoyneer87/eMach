
% D:\KangDH\Emlab_emach\mlxperPJT\JEET\dev4Summary_Plot3DJMesh.m
load('JEET_ref_e10_WirePeriodic_Load_18k_rgh_case1_JlossTable.mat')

%%Fig 4. 3D Jplot
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

%%plot Mesh
MPToolCSVFilePath='JEET_ref_e10_WirePeriodic_Load_18k_rgh_case1_J_MPtools.csv'
[model,pdeTriElements,pdeNodes,pdeQuadElements]  = nastran2PDEMesh(MPToolCSVFilePath,'mm');
pdeMeshMatPath=strrep('e10_JMAGWireTemplate90deg.dxf','.dxf','.mat')
quadMeshPath=[extractBefore(pdeMeshMatPath,'.mat'),'quad.mat']
save(pdeMeshMatPath,"model")
% save(quadMeshPath,"pdeQuadElements")

load(pdeMeshMatPath)
% load(quadMeshPath)
modelStruct=model;
model           =modelStruct.model
pdeNodes        =modelStruct.pdeNodes
pdeQuadElements =modelStruct.pdeQuadElements
MeshPlot=pdeplot(model.Mesh.Nodes,model.Mesh.Elements)
MeshPlot.Color=[0.80,0.80,0.80];  % grey

hold on
x = pdeNodes(1,:);
y = pdeNodes(2,:);
quadmesh(pdeQuadElements, x', y');
% DXFPath="D:\KangDH\Emlab_emach\mlxperPJT\JEET\From38100/e10_JMAGWireTemplate90deg.dxf";
% DXFtool(DXFPath)
ax=gca
DataAspectRatio(3)=2600
restoreView(ax,axisState,viewState,DataAspectRatio)
grid on
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
% exportgraphics(gcf,'JlossLegned.pdf','ContentType','vector')

% savefig(gcf,'test.fig')
% dev_plot3DVectorB

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
% close all