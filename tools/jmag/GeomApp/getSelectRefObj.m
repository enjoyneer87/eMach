function sel=getSelectRefObj(RefObj,geomApp)

%%
    AppDir=geomApp.GetAppDir;
    AppDirStr=split(AppDir,'/');
    if ~strcmp(AppDirStr{end},'Modeller')
     geomApp=geomApp.CreateGeometryEditor(0);
    end
    
%% mk selObj
    geomDocu=geomApp.GetDocument();
    sel=geomDocu.GetSelection;

%% Add RefObj

% sel.Add('face(TExtrudeSolid126+edge(TExtrudeSolid126+edge(TRegionItem83+TSketchArc25)))')
sel.AddReferenceObject(RefObj)

end