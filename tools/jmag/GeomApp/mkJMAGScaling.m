function mkJMAGScaling(app,RadialscaleFactor)

    NumModels=app.NumModels;
%% refModel Find
    
    for ModelIndex=1:NumModels
        ModelName=app.GetModel(ModelIndex-1).GetName;
        ModelNameList{ModelIndex}=ModelName;
    end
%% If there is refModel 
    refModel=ModelNameList{contains(ModelNameList,'ref','IgnoreCase',true)};
    if ~isempty(refModel)
        refModelObj=app.GetModel(refModel);
        Model.RestoreCadLink()
        geomApp=app.CreateGeometryEditor(0);
        geomAssem=geomApp.GetDocument().GetAssembly();
        NumItems=geomAssem.NumItems;
        for ItemNumIndex=1:NumItems
            ItemObj=geomAssem.GetItem(ItemNumIndex-1);
            if ItemObj.IsValid
            ItemName=ItemObj.GetName;
            ItemNameList{ItemNumIndex}=ItemName;
            end
        end
        %% If SCaling If there is no Scale    
        if ~contains(ItemNameList,'Assembly Scale','IgnoreCase',true)
            ScaleObj=geomAssem.CreateScale();
            ScaleObj.SetProperty("AllEditTargets ",true)
            ScaleObj.SetProperty("ScaleType ",0)
            ScaleObj.SetProperty("Factor", RadialscaleFactor)
            ScaleObj.SetProperty("CenterType", int32(2))
            app.GetCurrentModel().UpdateCadModel()
            ModelObj=app.GetCurrentModel;
            ModelObj.SetName(strrep(refModel,'ref','SC'))
            app.Save
        end
    end
    %% SetName
    PartStruct          =getJMAGDesignerPartStruct(app);
    PartTable           =struct2table(PartStruct);
    PartStructByType    =convertJmagPartStructByType(PartStruct);
    if isempty(PartStructByType.SlotTable)&isempty(PartStructByType.ConductorTable)
        ConductorPartTable = sortingConductorTableBySlot(PartTable,app);
        ConductorPartTable = ConductorPartTable(2:end,:);
        PartStructByType.SlotTable = ConductorPartTable;
    end
    % ConductorPartTable.Name=strrep(ConductorPartTable.Name,'Conductor','Stator/Conductor');
    changeJMAGPartNameTable(PartStructByType.SlotTable,app)
    %%
    MeshControlObj  = refModelObj.GetStudy(0).GetMeshControl();
    coreMeshPartObj = MeshControlObj.GetCondition("CorePart");

    MagnetMeshPartObj = MeshControlObj.GetCondition("MagnetPart");
    ConductorMeshPartObj = MeshControlObj.GetCondition("ConductorPart");

    refSizeTable    = mkDefaultMeshSizeTable();

    refSizeTable.coreMeshSize(1)             =coreMeshPartObj.GetValue("Size");
    refSizeTable.MagnetMeshSize(1)         =MagnetMeshPartObj.GetValue("Size");
    refSizeTable.ConductorMeshSize(1)       =ConductorMeshPartObj.GetValue("Size");
    ScaleSizeTable = varfun(@(x) RadialscaleFactor*x,refSizeTable);
    ScaleSizeTable.Properties.VariableNames=strrep(ScaleSizeTable.Properties.VariableNames,'Fun_','');
    MeshCondtionTable = setupMotorMesh(app,PartStructByType,ScaleSizeTable);
    ModelObj.GetStudy("e10_Coil_Load").GetCircuit().GetComponent("CS1").SetValue("Amplitude", "2*650.538238691624")
    app.GetModel("SC_e10_Coil").GetStudy("e10_Coil_Load").GetMeshControl().GetCondition("CorePart").SetValue("Size", "2*0.5")

    %%


end