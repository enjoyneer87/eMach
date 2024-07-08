function RegionData=getStatorGeomSketchData(app)
% Fields
% Name          (selection Class)
% ReferenceObj
% IdentifierName (ReferenceObj class)
% Id             (ReferenceObj class)
% Type           (selection Class)
%%
    geomApp=app.CreateGeometryEditor(0);
    geomApp.GetDocument().GetAssembly().GetItem("Stator").OpenSketch();
    geomDocu=geomApp.GetDocument();
    % geomView.SetSelectionFilter('Region')
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
    geomApp.GetDocument().GetAssembly().GetItem("Stator").CloseSketch();
end