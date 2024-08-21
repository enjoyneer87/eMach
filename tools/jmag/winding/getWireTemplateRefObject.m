function WireTemplateRefObj=getWireTemplateRefObject(app)
    Geom=app.CreateGeometryEditor(1);
    GeomDocu=Geom.GetDocument;
    % StatorItem=GeomDocu.GetAssembly().GetItem("Stator");
    % HairPin=StatorItem.GetItem("HairPin");
    HairPin=getWireTemplateObject(app);
    if HairPin.IsValid
    WireTemplateRefObj=GeomDocu.CreateReferenceFromItem(HairPin);
    WireTemplateRefObj.GetIdentifier
    end
end