function setGeomNameByIndex(RegionDataTable,Index2NameImport,geomApp)
% sel=mkSelectionObj(app);
%% check App or Geometry Editor

    AppDir=geomApp.GetAppDir;
    AppDirStr=split(AppDir,'/');
    if ~strcmp(AppDirStr{end},'Modeller')
    geomApp=geomApp.CreateGeometryEditor(0);
    geomApp.visible
    end

%% Define GeomSelection object (sel)
geomDocu=geomApp.GetDocument;
sel=geomDocu.GetSelection;
sel.Clear;

% geomApp=app.CreateGeometryEditor(0);
% geomView=geomApp.View();
% geomDocu=geomApp.GetDocument();

%% 
% Geom
sel.AddReferenceObject(RegionDataTable.ReferenceObj(Index2NameImport))
selCore=geomDocu.GetSelection;
    
    for ItemNum=1:selCore.Count
        whatis=selCore.Item(ItemNum-1);
        if whatis.IsValid
            % whatis.GetName
            whatis.SetName(RegionDataTable.Name{Index2NameImport})
        end
    end

sel.Clear;

end

% setRegionGeomNameWithAreaValue(Regiontable,AreaValue,RegionName,geomApp)
  % setGeomNamewithTableIndex(Regiontable,Index2NameImport,RegionName,geomApp)  
    % setGeomNameWithGeomReferenceObj(RefernceObj,RegionName,geomApp)

% updateGeomNameFromGeomTableWithTableIndex(RegionDataTable,Index2NameImport,geomApp)
% changeNameGeomSketchWithList(RegionDataTable,list4Change,app)
