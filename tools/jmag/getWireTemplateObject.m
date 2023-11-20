function WireTemplateObj=getWireTemplateObject(app)
    Geom=app.CreateGeometryEditor(1);
    GeomDocu=Geom.GetDocument;
    StatorItem=GeomDocu.GetAssembly().GetItem("Stator");
    WireTemplateObj=StatorItem.GetItem("HairPin");
end