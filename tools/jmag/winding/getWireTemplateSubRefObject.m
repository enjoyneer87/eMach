function RefObjStruct=getWireTemplateSubRefObject(app)
    Geom=app.CreateGeometryEditor(1);
    GeomDocu=Geom.GetDocument;
    % StatorItem.NumItems
    % GeomDocu.ConvertDesignerGeometryIndexId
    %% Get WireTemplate Item and Make ReferenceObj
    % StatorItem=GeomDocu.GetAssembly().GetItem("Stator");
    % HairPin=StatorItem.GetItem("HairPin");
    % if HairPin.IsValid
    % HairPinRefObj=GeomDocu.CreateReferenceFromItem(HairPin);
    % HairPinRefObj.GetIdentifier
    % HairPinRefObj.GetId
    % end
    HairPinRefObj=getWireTemplateRefObject(app);
    %% Get Sub RefObject of WireTemplate IdentifierName
    sel=mkSelectionObj(app);
    sel.AddReferenceObject(HairPinRefObj);
    
    selHairPinRef               =GeomDocu.GetSelection();
    GeomView=Geom.View;
    GeomView.ShowOnlySelectGeometries;

    sel                         =mkSelectionObj(app,1);
    selHairPinRef               =GeomDocu.GetSelection();
    CountReferenceObject        =selHairPinRef.CountReferenceObject;
    for RefObjIndex=1:CountReferenceObject
        zeroRef=selHairPinRef.GetReferenceObject(RefObjIndex-1);
        RefObjStruct(RefObjIndex).RefObj=zeroRef;
        RefObjStruct(RefObjIndex).IdentifierName=zeroRef.GetIdentifier;
        RefObjStruct(RefObjIndex).Id=zeroRef.GetId;
    end
    %%
end

