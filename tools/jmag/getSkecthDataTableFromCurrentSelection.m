function AssemObjStruct=getSkecthDataTableFromCurrentSelection(app)
   geomApp=app.CreateGeometryEditor(0);
   geomDocu=geomApp.GetDocument();
    %%
   sel      =mkSelectionObj(geomApp,1);
    NumSelections=sel.Count;
    AssemObjStruct=struct();
    for SelIndex=1:NumSelections
        Item=sel.Item(SelIndex-1);
        if Item.IsValid==1
        AssemObjStruct(SelIndex).ReferenceObj        =geomDocu.CreateReferenceFromItem(Item);
        AssemObjStruct(SelIndex).Name                =Item.GetName;
        AssemObjStruct(SelIndex).Type                =Item.GetScriptTypeName;
        AssemObjStruct(SelIndex).IdentifierName      =AssemObjStruct(SelIndex).ReferenceObj.GetIdentifier;
        AssemObjStruct(SelIndex).Id                  =AssemObjStruct(SelIndex).ReferenceObj.GetId;
        % sel.AddReferenceObject(RegionData(SelIndex).ReferenceObj)
        end
    end
    sel.Clear;
end
