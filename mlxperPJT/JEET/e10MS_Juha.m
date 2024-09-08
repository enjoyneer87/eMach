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
