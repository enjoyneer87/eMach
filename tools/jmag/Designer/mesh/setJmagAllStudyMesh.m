function setJmagAllStudyMesh(app,MeshStruct,PartStructNumStudies)

ConductorMeshSize=MeshStruct.ConductorMeshSize;
MagnetMeshSize   =MeshStruct.MagnetMeshSize;
CoreMeshSize     =MeshStruct.CoreMeshSize;
AutoDivision     =MeshStruct.AutoDivision;
AutoGapDivision  =MeshStruct.AutoGapDivision;
RadialDivision   =MeshStruct.RadialDivision;
CircumferentialDivision  =MeshStruct.CircumferentialDivision;
SlotConductorSetName="SlotConductor";

if nargin<3
    PartStructNumStudies=app.NumStudies;
end

%% Initialize Mesh
%% Initialize Condition FEM Coil
% curStudyObj=app.GetCurrentStudy
for StudyIndex=1:PartStructNumStudies
    curStudyObj=app.GetStudy(StudyIndex-1);
    MeshControlObj=curStudyObj.GetMeshControl();
    NumConditions= MeshControlObj.NumConditions;
    for ConditionIndex=1:NumConditions
        ConditionObj{ConditionIndex}=MeshControlObj.GetCondition(ConditionIndex-1);
        if ConditionObj{ConditionIndex}.IsValid
            ConditionObjName{ConditionIndex}=ConditionObj{ConditionIndex}.GetName;
            ConditionObjType{ConditionIndex}=ConditionObj{ConditionIndex}.GetType;
        end
    end
    for ConditionIndex=1:NumConditions
        MeshControlObj.DeleteCondition(ConditionObjName{ConditionIndex});
    end
end


% Mesh Condition
for StudyIndex=1:PartStructNumStudies
    curStudyObj=app.GetStudy(StudyIndex-1);
    app.SetCurrentStudy(curStudyObj)
    PartStruct       = getJMAGDesignerPartStruct(app);
    PartStructByType = convertJmagPartStructByType(PartStruct);
    MagnetTable=PartStructByType.MagnetTable;
    % 2.8 Mesh Seting
    % MeshControlObj 
    MeshControlObj=curStudyObj.GetMeshControl();
    % General Properties
    MeshControlObj.SetValue("MeshType", 1)
    MeshControlObj.SetValue("AirRegionDirection", 1)
    MeshControlObj.SetValue("AirRegionScaleY", 1.15)
    MeshControlObj.SetValue("AutoDivision", AutoDivision)
    MeshControlObj.SetValue("AutoGapDivision", AutoGapDivision)
    MeshControlObj.SetValue("RadialDivision", RadialDivision)
    MeshControlObj.SetValue("CircumferentialDivision", CircumferentialDivision)
    % Conductor
    ConductorMeshPartObj=curStudyObj.CreateCondition("Part", "ConductorPart"); 
    ConductorMeshPartObj.SetValue("Size", ConductorMeshSize)
    ConductorMeshPartObj.ClearParts()
    ConductorMeshPartObj.AddSetFromModel(SlotConductorSetName,0)
    % core
    coreMeshPartObj=MeshControlObj.CreateCondition("Part", "CorePart");
    coreMeshPartObj.SetValue("Size",CoreMeshSize)
    coreMeshPartObj.ClearParts()
    coreMeshPartObj.AddPart("Stator/StatorCore")
    coreMeshPartObj.AddPart("Rotor/RotorCore")
    
    % Magnet
    MagnetMeshPartObj=MeshControlObj.CreateCondition("Part", "MagnetPart");
    MagnetMeshPartObj.SetValue("Size",MagnetMeshSize)
    MagnetMeshPartObj.ClearParts()
    
    %MagnetTable
    for MagnetIndex=1:height(MagnetTable)
    MagnetMeshPartObj.AddPart(MagnetTable.Name{MagnetIndex})
    end

    % RotationPeriodicMeshAutomatic
    MeshControlObj.CreateCondition("RotationPeriodicMeshAutomatic", "RPMesh")

    %meshTotalPropertyTable
    % meshTotalPropertyTable=MeshControlObj.GetPropertyTable;
    % meshTotalPropertyTable=char2CategoricalPropertiesTable(meshTotalPropertyTable);
    % % MeshControl Condition
    % NumConditions=MeshControlObj.NumConditions   ;
    % MeshCondtionTable=table();
    % for MeshConditionIndex=1:NumConditions
    %     MeshCondtionObj=MeshControlObj.GetCondition(MeshConditionIndex-1);
    %     MeshCondtionTable.MeshCondition(MeshConditionIndex)             =MeshCondtionObj;
    %     MeshCondtionTable.CondtionType{MeshConditionIndex}              ={MeshCondtionObj.GetType};
    %     MeshCondtionTable.Name{MeshConditionIndex}                      ={MeshCondtionObj.GetName};
    %     MeshCondtionTable.MeshCondtionPropertyTable(MeshConditionIndex) ={char2CategoricalPropertiesTable(MeshCondtionObj.GetPropertyTable)};
    %     MeshCondtionTable.Parts(MeshConditionIndex)                     ={MeshCondtionObj.GetParts};
    % end
end