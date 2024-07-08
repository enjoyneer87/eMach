function RefObjListTable=getAllRefObjListTableWithSel(geomApp)
    %% [Check]
    % getSkecthDataTableFromCurrentSelection >> getRefObjFromCurrentSelection
    AppDir=geomApp.GetAppDir;
    AppDirStr=split(AppDir,'/');
    if ~strcmp(AppDirStr{end},'Modeller')
    geomApp=geomApp.CreateGeometryEditor(0);
    end
   %% selection
   % geomDocu     =geomApp.GetDocument;
   sel          =mkSelectionObj(geomApp,1);
   NumSelections=sel.CountReferenceObject;
    %% 
    AssemObjStruct=struct();
    for SelIndex=1:NumSelections
             tempRefObj                =sel.GetReferenceObject(SelIndex-1);          
             tempRefObjIdName          =tempRefObj.GetIdentifier;
            if ~contains(tempRefObjIdName, 'Plane','IgnoreCase',true) && ~contains(tempRefObjIdName, 'Scale','IgnoreCase',true) 
            AssemObjStruct(SelIndex).ReferenceObj        =tempRefObj;
            AssemObjStruct(SelIndex).IdentifierName      =tempRefObjIdName;
            AssemObjStruct(SelIndex).Id                  =tempRefObj.GetId;
            end
    end
    sel.Clear;


    RefObjListTable=struct2table(AssemObjStruct);
end
