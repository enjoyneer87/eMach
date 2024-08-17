function setGeomNameByIndex(RegionDataTable,Index4ChangeObject,geomApp)
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

% RegionDataTable.sketchItemObj{Index4ChangeObject}.SetName(RegionName);
RegionDataTable.sketchItemObj{Index4ChangeObject}.SetProperty("Name", RegionName);

end
% sel.AddReferenceObject(refObj)
% selCore=geomDocu.GetSelection;

% %% Define GeomSelection object (sel)
% geomDocu=geomApp.GetDocument;
% sel=geomDocu.GetSelection;
% sel.Clear;

% geomApp=app.CreateGeometryEditor(0);
% geomView=geomApp.View();
% geomDocu=geomApp.GetDocument();

%% 
% % Geom
% if iscell(RegionDataTable.ReferenceObj(Index4ChangeObject))
% refObj=RegionDataTable.ReferenceObj{Index4ChangeObject};
% else
% refObj=RegionDataTable.ReferenceObj(Index4ChangeObject);
% end


    

% % geomApp.GetDocument().GetAssembly().GetItem(u"Stator").GetItem(u"Region.4").SetProperty(u"Name", u"conductor")
% 
%     for ItemNum=1:selCore.Count
%         whatis=selCore.Item(int32(ItemNum-1));
%         if whatis.IsValid
%             % whatis.GetName
%             if iscell(RegionDataTable.Name(Index4ChangeObject))
%                 RegionName=RegionDataTable.Name{Index4ChangeObject};
%             else
%                 RegionName=RegionDataTable.Name(Index4ChangeObject);
%             end
%             whatis.SetName(RegionName)
%         end
%     end

% sel.Clear;

% end

% setRegionGeomNameWithAreaValue(Regiontable,AreaValue,RegionName,geomApp)
  % setGeomNamewithTableIndex(Regiontable,Index2NameImport,RegionName,geomApp)  
    % setGeomNameWithGeomReferenceObj(RefernceObj,RegionName,geomApp)

% updateGeomNameFromGeomTableWithTableIndex(RegionDataTable,Index2NameImport,geomApp)
% changeNameGeomSketchWithList(RegionDataTable,list4Change,app)
