geomApp = app.CreateGeometryEditor();

Numports=getPCRDPPortNumber
if Numports==38002
DXFPath="Z:/Simulation/JEETACLossValid_e10_v24/refModel/e10_JMAG.dxf";
DXFPath="Z:/Simulation/JEETACLossValid_e10_v24/refModel/e10_JMAGWireTemplate90deg.dxf";
DXFPath="Z:/Simulation/JEETACLossValid_e10_v24/refModel/e10_SCL_ConductorModel.dxf";
DXFPath="Z:/Simulation/JEETACLossValid_e10_v24/refModel/e10_REF_ConductorModel.dxf";
DXFPath="Z:/Simulation/JEETACLossValid_e10_v24/refModel/e10_REF_ConductorModel.dxf";
else
DXFPath="D:\KangDH\Emlab_emach\mlxperPJT\JEET\From38100/e10_JMAGWireTemplate90deg.dxf";
end
geomApp.GetDocument().ExportData(DXFPath);
hold on
DXFtool(DXFPath)
formatterFigure4Paper('double','2x2')
StepList=[1,44,86,120]
stepList=StepList;
%% Abs Table/XTable/YTable
for caseInd=1:1
    for stepIndex=1:length(stepList)
        stepData=stepList(stepIndex);
        PosTable=FieldData{caseIndex}.positionTable; 
        % figure(1) % Abs
        AbsTable=FieldData{caseIndex}.AbsTable;
        ValueVecPerNode=AbsTable(:,stepData).Variables;
        
        [theta,r]=cart2pol(PosTable.("Position X"),PosTable.("Position Y"));
        firstSlotIndex=theta<deg2rad(45/6);

        xPos2Plot=(PosTable.("Position X")(firstSlotIndex));
        yPos2Plot=(PosTable.("Position Y")(firstSlotIndex));

        Value2Plot=ValueVecPerNode(firstSlotIndex);
        if stepData==1
        stem3(xPos2Plot,yPos2Plot,Value2Plot,'O:','DisplayName',['step',num2str(stepData)],'LineWidth',2)
        % stem(yPos2Plot,Value2Plot,'O:','DisplayName',['step',num2str(stepData)],'LineWidth',2)

        elseif stepData==44
        stem3(xPos2Plot,yPos2Plot,Value2Plot,'x--','DisplayName',['step',num2str(stepData)],'LineWidth',2);
        % stem(yPos2Plot,Value2Plot,'x--','DisplayName',['step',num2str(stepData)],'LineWidth',2);

        elseif stepData==88
        stem3(xPos2Plot,yPos2Plot,Value2Plot,'Diamond:','DisplayName',['step',num2str(stepData)],'LineWidth',2);
        % stem(yPos2Plot,Value2Plot,'Diamond:','DisplayName',['step',num2str(stepData)],'LineWidth',2);

        elseif stepData==120
        stem3(xPos2Plot,yPos2Plot,Value2Plot,'^:','DisplayName',['step',num2str(stepData)],'LineWidth',2);
        % stem(yPos2Plot,Value2Plot,'^:','DisplayName',['step',num2str(stepData)],'LineWidth',2);

        end
        % Figure(2) % Rtable
        % 
        % Figure(3) % TTable
        hold on
    end
        set(gca, 'XDir', 'reverse');

end
%%Plot Mesh
%parse Mesh
[theta,r]=cart2pol(model.Mesh.Nodes(1,:),model.Mesh.Nodes(2,:));
firstSlotIndex=theta<deg2rad(45/6*1.1);
NodeIds=find(~firstSlotIndex);
model.Mesh.Elements;
pdemesh(model)
hold on
%% Element Cell
num_array = (1:1:length(model.Mesh.Elements));
% 숫자 배열을 문자열 cell 배열로 변환
str_cell = arrayfun(@num2str, num_array, 'UniformOutput', false);


PartStruct          =getJMAGDesignerPartStruct(app);
PartStruct=getEdgeVertexIdwithXYZCheck(PartStruct,app);   
PartStructByType    =convertJmagPartStructByType(PartStruct);
ROD=PartStructByType.RotorCoreTable.VertexMaxRPos;
STelemIDs = findElements(model.Mesh,"radius",[0,0],ROD*1.001);
elemIDs = findElements(model.Mesh,"attached",NodeIds);

ElemIDsCellByRadius = arrayfun(@num2str, STelemIDs, 'UniformOutput', false);
ElemIDsCellByTheta   = arrayfun(@num2str, elemIDs, 'UniformOutput', false);

[uniqueStringsInCell1, uniqueStringsInCell2, nonUniqueStrings] =findUniqueAndNonUniqueStrings(str_cell,ElemIDsCellByRadius);
[ThetaUniqueString1, ThetaUniqueString2, nonUniqueStrings]     =findUniqueAndNonUniqueStrings(str_cell,ElemIDsCellByTheta);

[str1, str2, nonUniqueStrings] =findUniqueAndNonUniqueStrings(uniqueStringsInCell1,ThetaUniqueString1);

%%
num_array = str2double(nonUniqueStrings);
stator.Mesh.Elements=model.Mesh.Elements(:,num_array);
statorE = createpde("electromagnetic");
stEle   = stator.Mesh.Elements;
geometryFromMesh(statorE,model.Mesh.Nodes,stEle);

% pdemesh(statorE)
MeshPlot=pdeplot(statorE.Mesh.Nodes,statorE.Mesh.Elements);
MeshPlot.Color=[0.80,0.80,0.80];  % grey

%% entitiy plot

% plotEntitiesStruct(StatorDxf)

entitiesStatorStruct = readDXF(DXFPath);
% DXFtool(dxfFiles{1})
% entitiesStatorStruct = arrayfun(@(x) setfield(x, 'layer', 'stator'), entitiesStatorStruct);
StatorDxf = filterEntitiesByAngle(entitiesStatorStruct, 90);
plotEntitiesStruct(StatorDxf)

entitiesStatorStruct = readDXF(dxfFiles{end-1});
entitiesStatorStruct = arrayfun(@(x) setfield(x, 'layer', 'stator'), entitiesStatorStruct);
ConductorDXF = filterEntitiesByAngle(entitiesStatorStruct, 7.5);
plotEntitiesStruct(ConductorDXF)
% STNodeIDs =findNodes(model.Mesh,"radius",[0,0],ROD)
% MeshPlot=pdeplot(model.Mesh.Nodes,model.Mesh.Elements);

hold on
MeshPDEtoolForm=model.Mesh;
[PetFor.p,PetFor.e,PetFor.t]=MeshPDEtoolForm.meshToPet();
PetFor.t(4,:)=[];
msh=PetFor;
x = pdeNodes(1,:);
y = pdeNodes(2,:);
quadmesh(pdeQuadElements, x, y);
centerAllFigures

ax=gca
ax.DataAspectRatio=[1 1 0.1]

ax.XLim=[ROD ROD+12]
ax.YLim=[-2 12]

formatterFigure4Paper('double','2x2')