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
    GeomAssem=GeomDocu.GetAssembly();
    StatorItemobj=GeomAssem.GetItem("Stator");
    if ~StatorItemobj.IsValid
        NumItems=GeomAssem.NumItems;
        for ItemIndex=1:NumItems
        StatorObjList{ItemIndex}=GeomAssem.GetItem(int32(ItemIndex)-1); 
            if StatorObjList{ItemIndex}.IsValid
                StatorObjName{ItemIndex}=StatorObjList{ItemIndex}.GetName;
                if contains(StatorObjName{ItemIndex},'stator','IgnoreCase',true)
                    StatorItemobj=StatorObjList{ItemIndex};
                end
            end
        end
    end

    WireTemplateObj=StatorItemobj.GetItem("HairPin");
    if ~WireTemplateObj.IsValid
    WireTemplateObj=StatorItemobj.GetItem('Wire Template');
    end

    if WireTemplateObj.IsValid
    WireTemplateObj.GetName
    end
end