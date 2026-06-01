% Coil모델
% 무부하 파형, 토크, 전류위상각 산출
addpath(genpath(pwd))
app=callJmag
app.Show
jprojPath="Z:\Simulation\JEETACLossValid_e10_v24\refModel\e10_ConductorModel.jproj";
app.Load(jprojPath)
% 자속파형, 추출
% 인덕턴스 및 파라미터 추출
% calcACLossModel plot


%% SetName
setJmagNameByHier(app)

%
PartStruct          =getJMAGDesignerPartStruct(app);
idx=findMatchingIndexInStruct(PartStruct,'Name','Stator/Region');
WireStruct=PartStruct(idx);
idx=contains({WireStruct.Name},'StatorCore',IgnoreCase=true);
WireStruct=WireStruct(~idx);

%% FEM Coil Setting
setJmagAllStudyFEMCoil(app)

%% mkCoil Circuit
NumAppStudies=app.NumStudies;
for StudyIndex=1:NumAppStudies
    % curStudyObj=app.GetStudy(StudyIndex-1); 
    app.SetCurrentStudy(StudyIndex-1)
    mkJmag3phaseCoilSinCircuit(app)  % Winding
end
% set Input
RMSCurrent=460;
ParallelPath=2;
SeriesturnInSlot=4;
setJmagCircuitInputByEqNStudyName(app,RMSCurrent,ParallelPath)

% set Turn N Rph
RphActive=devsetFEMCoilTurnNRph(app,4,2);

%% Turn OFF Eddy Current
NumModels=app.NumModels;
for ModelIndex=1:NumModels
    ModelObj        =app.GetModel(ModelIndex-1);
    NumStudies      =ModelObj.NumStudies;
    for StudyIndex=1:NumStudies
        PartStruct       = getJMAGDesignerPartStruct(app);
        PartStructByType = convertJmagPartStructByType(PartStruct);
        curStudyObj=ModelObj.GetStudy(StudyIndex-1);   
        for PartIndex=1:height(PartStructByType.SlotTable)
            curStudyObj.SetMaterialByName(PartStructByType.SlotTable.Name{PartIndex},"Air")
        end
    end
end

for ModelIndex=1:NumModels
    ModelObj        =app.GetModel(ModelIndex-1);
    NumStudies      =ModelObj.NumStudies;
    for StudyIndex=1:NumStudies
        curStudyObj=ModelObj.GetStudy(StudyIndex-1);   
        MeshControlObj=curStudyObj.GetMeshControl();
        if MeshControlObj.GetConditionByType("SkinDepth",0).IsValid
            MeshControlObj.DeleteConditionByType("SkinDepth",0)
        end
    end
end

NumAppStudies=app.NumStudies;
for StudyIndex=1:NumAppStudies
    curStudyObj=app.GetStudy(StudyIndex-1);   
    [propertiesTableWithValue{StudyIndex}, stepTable{StudyIndex}]=getJMagStudyProperties(curStudyObj);
end
%% Mesh 
MeshStruct=defJMAGMeshStruct();
setJmagAllStudyMesh(app,MeshStruct,2)

%% mk case with Speed
speedList= [1000:2000:14000];
NumCase=length(speedList);
for StudyIndex=1:NumAppStudies
    curStudyObj=app.GetStudy(StudyIndex-1);   
    curStudyObj=app.GetStudy(StudyIndex-1);   

    DTObj=curStudyObj.GetDesignTable();
    curNumCases=DTObj.NumCases;
    if ~curNumCases==NumCase
        for caseIndex=1:curNumCases-1
            DTObj.RemoveCase(curNumCases)  % delete from case 2
        end
        DTObj.AddCases(NumCase-1)
        speedParaIndex=DTObj.GetParameterIndex('speed');
        for CaseIndex=1:NumCase
            DTObj.SetValue(CaseIndex,speedParaIndex,speedList(CaseIndex))
        end
    end
end
%% end
%%%%%%%%%% skin Depth Model
% delta=calcSkinDepth(omega2freq(rpm2OmegaE(1000,4))) % 2.25594 -;
% 
% %% Mk scale
% mkJMAGScaling(app,RadialscaleFactor)
% 
% 
% 
% for StudyIndex=1:NumStudies
%     curStudyObj=app.GetStudy(int32(StudyIndex)-1);
%     StudyName=curStudyObj.GetName;
%     RTableObj=curStudyObj.GetResultTable;
%     if RTableObj.IsValid
%         NumTables=RTableObj.NumTables;
%         ResultFilePath{StudyIndex} =fullfile(PJTPDir,[StudyName,'.csv']);
%         RTableObj.WriteAllCaseTables(ResultFilePath{StudyIndex},'Steps')
%     end
% end

PartStruct=getJMAGDesignerPartStruct(app);
idx=findMatchingIndexInStruct(PartStruct,'Name','Wire')
WireStruct=PartStruct(idx);
%% Get Wire Element and Node ID
for Index=1:length(WireStruct)
    WireIndex=WireStruct(Index).partIndex;
    [WireStruct(Index).ElementId, WireStruct(Index).NodeID]=getMeshData(app,WireIndex)
end

PartIdList=[WireStruct.partIndex];
exportFilePath=exportFieldData2CSV(app,'B','JEET',PartIdList,'SCL','_Load');

%% Manual Export
MPToolCSVFilePath='Z:\Simulation\JEETACLossValid_e10_v24\refModel\ExportMPtools\MSConductorModel.csv'
[model,pdeTriElements,pdeNodes,pdeQuadElements]  = nastran2PDEMesh(MPToolCSVFilePath,'mm');
% figure(1)
% 색상을 설정합니다.
% 각 영역을 시각화하여 구분합니다.
% pdegplot(model, 'FaceLabels', 'on', 'EdgeLabels', 'on');
title('Geometry with Face Labels');
numFaces = model.Geometry.NumFaces;
colors = lines(numFaces); % 각 Face에 대해 다른 색상을 생성합니다.
figure(1);
pdemesh(model)
x = pdeNodes(1,:);
y = pdeNodes(2,:);
hold on
quadmesh(pdeQuadElements, x, y);
centerAllFigures
% 색상을 설정합니다.
line_handles = findobj(gca, 'Type','line');
set(line_handles, 'Color', [0.8,0.8,0.8]); % 예: 검은색


%% Read B Table
LoadexportFilePath=exportFilePath(contains(exportFilePath,'_Load','IgnoreCase',true));
for CaseIndex=1:length(LoadexportFilePath)
    filePath=LoadexportFilePath{CaseIndex};
    FieldData{CaseIndex}=readJMAGFieldTable(filePath);
end
StepList=FieldData{1}.AbsTable.Properties.VariableNames;

caseIndex=1
[thetaPosAll,RPosAll]=cart2pol(FieldData{caseIndex}.positionTable.("Position X"),FieldData{caseIndex}.positionTable.("Position Y"))
MaxThetaIndex=find(difftol(thetaPosAll,max(thetaPosAll),1e-2)&difftol(RPosAll,min(RPosAll),1e-2));
MinThetaIndex=find(difftol(thetaPosAll,min(thetaPosAll),1e-2)&difftol(RPosAll,min(RPosAll),1e-2));


plot([0:3:360],FieldData{caseIndex}.AbsTable(MaxThetaIndex,361:481).Variables,'*--','DisplayName','Left')
hold on
plot([0:3:360],FieldData{caseIndex}.AbsTable(MinThetaIndex,361:481).Variables,'^-','DisplayName','Right')
formatterFigure4Paper('double','2x2')

%
freqList=rpm2freqE(rpmList,4)


Fq=ACLoss

%% B Plot
StepList=[1,44,86,120]
stepList=StepList;
%% Abs Table/XTable/YTable
for caseIndex=1:1
    for stepIndex=1:length(stepList)
        stepData=stepList(stepIndex)
        PosTable=FieldData{caseIndex}.positionTable; 
        % figure(1) % Abs
        table2Plot=FieldData{caseIndex}.thetaTable;
        ValueVecPerNode=table2Plot(:,stepData).Variables;
        ValueVecPerNode=abs(ValueVecPerNode)
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
        set(gca, 'XDir');

end

% DXF
entitiesStatorStruct = readDXF(DXFPath);
StatorDxf = filterEntitiesByAngle(entitiesStatorStruct, 90);
plotEntitiesStruct(StatorDxf)
% ROD 
PartStruct          =getJMAGDesignerPartStruct(app);
PartStruct=getEdgeVertexIdwithXYZCheck(PartStruct,app);   
PartStructByType    =convertJmagPartStructByType(PartStruct);
ROD=PartStructByType.RotorCoreTable.VertexMaxRPos;
ax=gca
ax.DataAspectRatio=[1 1 0.1]

ax.XLim=[ROD ROD+12]
ax.YLim=[-2 12]

formatterFigure4Paper('double','2x2')
%% Juha calc


REFdimensions=[3.7, 1.6 5.30333]
NtCoil=4
rpmList=[50:50:950 1000:1000: 20000]
freqE = rpm2freqE(rpmList,4)

kr=calcHybridJouleLossJuHa(REFdimensions,NtCoil,freqE)

per_a

coeff = 2 * RphActive * 460^2;
Pjoule = coeff * (1 + kr .* freqE.^2)/1000;

Pjoule_density[0, :] = Pjoule / (periodicity * Lst * np_sum(Se))

out.geo.per_a
plot(rpmList,Pjoule)