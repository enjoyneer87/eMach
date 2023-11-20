function RegionData=getSkecthDataTableFromCurrentSelection(app)
    geomApp=app.CreateGeometryEditor(0);
   geomDocu=geomApp.GetDocument();
    %%
   sel      =mkSelectionObj(app,1);
    NumSelections=sel.Count;
    RegionData=struct();
    for SelIndex=1:NumSelections
        Item=sel.Item(SelIndex-1);
        if Item.IsValid==1
        RegionData(SelIndex).ReferenceObj        =geomDocu.CreateReferenceFromItem(Item);
        RegionData(SelIndex).Name                =Item.GetName;
        RegionData(SelIndex).Type                =Item.GetScriptTypeName;
        RegionData(SelIndex).IdentifierName      =RegionData(SelIndex).ReferenceObj.GetIdentifier;
        RegionData(SelIndex).Id                  =RegionData(SelIndex).ReferenceObj.GetId;
        % sel.AddReferenceObject(RegionData(SelIndex).ReferenceObj)
        end
    end
    sel.Clear;
end
