function WireTemplateObj=getWireTemplateObject(geomApp)
%% check App or Geometry Editor
    AppDir=geomApp.GetAppDir;
    AppDirStr=split(AppDir,'/');
    if ~strcmp(AppDirStr{end},'Modeller')
    geomApp=geomApp.CreateGeometryEditor(0);
    geomApp.visible
    end
%% get WireTemplate Obj
    GeomDocu=geomApp.GetDocument;
    StatorItem=GeomDocu.GetAssembly().GetItem("Stator");
    
    WireTemplateObj=StatorItem.GetItem("HairPin");
    if ~WireTemplateObj.IsValid
    WireTemplateObj=StatorItem.GetItem('Wire Template');
    end

    if WireTemplateObj.IsValid
    WireTemplateObj.GetName
    end
end