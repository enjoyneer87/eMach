function refObjTable=getStatorGeomSketchRefObj(app)
% Fields
% Name          (selection Class)
% ReferenceObj
% IdentifierName (ReferenceObj class)
% Id             (ReferenceObj class)
% Type           (selection Class)
%%
    refObjTable=struct();
    geomApp=app.CreateGeometryEditor(0);
    geomApp.GetDocument().GetAssembly().GetItem("Stator").OpenSketch();
    geomDocu=geomApp.GetDocument();
    % geomView.SetSelectionFilter('Region')
    %% Selection Obj

    sel      =mkSelectionObj(app,1);
    NumSelections=sel.Count;
    for SelIndex=1:NumSelections
        %% ItemObj
        Item=sel.Item(SelIndex-1);
        if Item.IsValid==1
        %% RefObj    
        refObjTable(SelIndex).ReferenceObj        =geomDocu.CreateReferenceFromItem(Item);
        refObjTable(SelIndex).Name                =Item.GetName;
        refObjTable(SelIndex).Type                =Item.GetScriptTypeName;
        refObjTable(SelIndex).IdentifierName      =refObjTable(SelIndex).ReferenceObj.GetIdentifier;
        refObjTable(SelIndex).Id                  =refObjTable(SelIndex).ReferenceObj.GetId;
        % sel.AddReferenceObject(RegionData(SelIndex).ReferenceObj)
        end
    end
    sel.Clear;
    geomApp.GetDocument().GetAssembly().GetItem("Stator").CloseSketch();
end