function RegionDataTable=getGeomNameByIndex(RegionDataTable,Index4ChangeObject,geomApp)
% sel=mkSelectionObj(app);
%% check App or Geometry Editor

    AppDir=geomApp.GetAppDir;
    AppDirStr=split(AppDir,'/');
    if ~strcmp(AppDirStr{end},'Modeller')
    geomApp=geomApp.CreateGeometryEditor(0);
    geomApp.visible
    end

    %% change Name
if iscell(RegionDataTable.Name(Index4ChangeObject))
    RegionName=RegionDataTable.Name{Index4ChangeObject};
else
    RegionName=RegionDataTable.Name(Index4ChangeObject);
end

RegionDataTable.Name{Index4ChangeObject} =RegionDataTable.sketchItemObj{Index4ChangeObject}.GetName;
RegionDataTable.sketchItemName=RegionDataTable.Name;

end

% refObj
% %% Define GeomSelection object (sel)
% geomDocu=geomApp.GetDocument;
% sel=geomDocu.GetSelection;
% sel.Clear;
% 
% % geomApp=app.CreateGeometryEditor(0);
% % geomView=geomApp.View();
% % geomDocu=geomApp.GetDocument();
% 
% %% 
% % Geom
% if iscell(RegionDataTable.ReferenceObj(Index2NameImport))
%     refObj=RegionDataTable.ReferenceObj{Index2NameImport};
% else
%     refObj=RegionDataTable.ReferenceObj(Index2NameImport);
% end
% sel.AddReferenceObject(refObj)
% selCore=geomDocu.GetSelection;
% 
%     for ItemNum=1:selCore.Count
%         whatis=selCore.Item(ItemNum-1);
%         if whatis.IsValid
%             % whatis.GetName
%             RegionDataTable.Name{Index2NameImport}=whatis.GetName();
%         end
%     end
% 
% sel.Clear;

% end