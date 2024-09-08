function MeshCondtionTable = setupMotorMesh(app,PartStructByType,MeshSizeStruct)
    % setupMeshConditions: 각 Study에 대한 메쉬 조건을 설정하고 결과 테이블을 반환합니다.
    %
    % 입력:
    %   
    %  
    %   
    %   - SlotConductorSetName: 슬롯 전도체 세트 이름
    %   - ConductorMeshSize: 전도체 메쉬 크기
    %   - MagnetTable: 자석 테이블
    %
    % 출력:
    %   - MeshCondtionTable: 메쉬 조건 테이블
    
    %
    % MeshSizeStruct=ScaleSizeTable
    MeshCondtionTable = table(); % 결과 테이블 초기화
    Model=app.GetCurrentModel;
    SetListObj=Model.GetSetList;
    

    %% default
    MagnetTable         =PartStructByType.MagnetTable;
    AirRegionScaleY     =1.15;

    if nargin<3
    coreMeshSize        =0.5;
    ConductorMeshSize   =1;
    MagnetMeshSize      =1;
    skinDepthFixed      =0.4;
    SkinMeshDivision    =4;
    SkinMeshCommonRatio =1;
    else
    coreMeshSize        =MeshSizeStruct.coreMeshSize      ;
    ConductorMeshSize   =MeshSizeStruct.ConductorMeshSize ;
    MagnetMeshSize      =MeshSizeStruct.MagnetMeshSize    ;
    skinDepthFixed      =0.4;
    SkinMeshDivision    =4;
    SkinMeshCommonRatio =1;
    end
    %% SlotConductorSetName
    NumSet=SetListObj.NumSet;
    if SetListObj.IsValid
        for SetIndex=1:NumSet
            SetObj=SetListObj.GetSet(NumSet);
            if SetObj.IsValid
                setName=SetObj.GetName;
                if contains(setName,'Slot','IgnoreCase',true)
                SlotConductorSetName=setName;
                end
            end
        end
    end
    %% 시작
    NumStudies=Model.NumStudies;
    for StudyIndex = 1:NumStudies
        % 현재 Study 객체 설정
        curStudyObj = Model.GetStudy(StudyIndex - 1);
        rpm  = curStudyObj.GetDesignTable().GetEquation("speed").GetValue;
        NumPoles  = curStudyObj.GetDesignTable().GetEquation("POLES").GetValue;
        app.SetCurrentStudy(curStudyObj);        
        % 2.8 Mesh Setting
        % MeshControlObj 
        MeshControlObj = curStudyObj.GetMeshControl();
        
        % General Properties
        MeshControlObj.SetValue("MeshType", 1);
        MeshControlObj.SetValue("AirRegionDirection", 1);
        MeshControlObj.SetValue("AirRegionScaleY", AirRegionScaleY);
        
        %% init
        if MeshControlObj.IsValid
            NumConditionsMeshCondition=MeshControlObj.NumConditions;
            
            for MeshConditionIndex=1:40
                if MeshControlObj.GetCondition(MeshConditionIndex-1).IsValid
                   MeshConditionName{MeshConditionIndex}=MeshControlObj.GetCondition(MeshConditionIndex-1).GetName;
                end
            end

            for MeshConditionIndex=1:NumConditionsMeshCondition
                   MeshControlObj.DeleteCondition(MeshConditionName{MeshConditionIndex});        
            end
        end
        %% SkinDepth 설정
        omegaE = rpm2OmegaE(rpm, NumPoles/2);
        SkinDepth_delta_inmm = calcSkinDepth(omegaE);
        
        if all(~contains(curStudyObj.GetName,'Coil','IgnoreCase',true),~contains(curStudyObj.GetName,'MS','IgnoreCase',true))
            if MeshControlObj.GetCondition('ConductorSkinDepth').IsValid
                ConductorSkinDepthObj = MeshControlObj.GetCondition("ConductorSkinDepth");
            else
                ConductorSkinDepthObj = MeshControlObj.CreateCondition("SkinDepth", "ConductorSkinDepth");        
            end
            ConductorSkinDepthObj.SetValue("Depth", skinDepthFixed);
            ConductorSkinDepthObj.SetValue("Division", SkinMeshDivision);
            ConductorSkinDepthObj.SetValue("CommonRatio", SkinMeshCommonRatio);
            ConductorSkinDepthObj.ClearParts();
            if ~exist('SlotConductorSetName','var')
            SlotConductorSetName='SlotConductor';
            end
            ConductorSkinDepthObj.AddSetFromModel(SlotConductorSetName, 0);  
        else 
            if MeshControlObj.GetCondition('ConductorSkinDepth').IsValid
                ConductorSkinDepthObj = MeshControlObj.GetCondition("ConductorSkinDepth");
                ConductorSkinDepthObj.delete;
            end
        end

        %% 기본메쉬
        % Conductor 메쉬 설정
        ConductorMeshPartObj = curStudyObj.CreateCondition("Part", "ConductorPart");
        ConductorMeshPartObj.SetValue("Size", ConductorMeshSize);
        ConductorMeshPartObj.ClearParts();
        if ~exist('SlotConductorSetName','var')
            SlotConductorSetName='SlotConductor';
        end
        ConductorMeshPartObj.AddSetFromModel(SlotConductorSetName, 0);
        
        % Core 메쉬 설정
        coreMeshPartObj = MeshControlObj.CreateCondition("Part", "CorePart");
        coreMeshPartObj.SetValue("Size", coreMeshSize);
        coreMeshPartObj.ClearParts();
        coreMeshPartObj.AddPart("Stator/StatorCore");
        coreMeshPartObj.AddPart("Rotor/RotorCore");
        
        % Magnet 메쉬 설정
        MagnetMeshPartObj = MeshControlObj.CreateCondition("Part", "MagnetPart");
        MagnetMeshPartObj.SetValue("Size", MagnetMeshSize);
        MagnetMeshPartObj.ClearParts();
        
        % MagnetTable에서 각 자석에 대해 추가
        for MagnetIndex = 1:height(MagnetTable)
            MagnetMeshPartObj.AddPart(MagnetTable.Name{MagnetIndex});
        end
        
        % meshTotalPropertyTable 가져오기
        meshTotalPropertyTable = MeshControlObj.GetPropertyTable();
        meshTotalPropertyTable = char2CategoricalPropertiesTable(meshTotalPropertyTable);
        if ~MeshControlObj.GetConditionByType('RotationPeriodicMeshAutomatic',0).IsValid
        RPMeshObj=MeshControlObj.CreateCondition("RotationPeriodicMeshAutomatic", "RPMesh");
        % RPMeshObj.GetName
        end
        % MeshControl Condition 테이블 생성
        NumConditions = MeshControlObj.NumConditions;
        for MeshConditionIndex = 1:NumConditions
            MeshCondtionObj = MeshControlObj.GetCondition(MeshConditionIndex - 1);
            MeshCondtionTable.MeshCondition(MeshConditionIndex)             = MeshCondtionObj;
            MeshCondtionTable.CondtionType{MeshConditionIndex}              = MeshCondtionObj.GetType;
            MeshCondtionTable.Name{MeshConditionIndex}                      = MeshCondtionObj.GetName;
            MeshCondtionTable.MeshCondtionPropertyTable(MeshConditionIndex) = {char2CategoricalPropertiesTable(MeshCondtionObj.GetPropertyTable)};
            MeshCondtionTable.Parts(MeshConditionIndex)                     = {MeshCondtionObj.GetParts};
        end
    end
end