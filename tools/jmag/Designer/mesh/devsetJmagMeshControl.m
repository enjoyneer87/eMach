function devsetJmagMeshControl(Model)
if contains(class(Model),'designer')
Model=Model.GetCurrentModel();
end

ObjMeshControl=Model.GetStudy(1).GetMeshControl();
MeshPropertyNames=ObjMeshControl.GetPropertyNames
ConditionTypeNames=ObjMeshControl.GetConditionTypeNames;
ObjMeshControl.GetPropertyTable
.SetValue("2dMeshingMethod", 3)

end