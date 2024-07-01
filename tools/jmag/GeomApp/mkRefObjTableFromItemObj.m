function refVertexTable=mkRefObjTableFromItemObj(VertexObj,geomApp)
    AppDir=geomApp.GetAppDir;
    AppDirStr=split(AppDir,'/');
    if ~strcmp(AppDirStr{end},'Modeller')        
    geomApp=geomApp.CreateGeometryEditor(0);
    end
    geomDocu=geomApp.GetDocument;
    refVertexTable=table();
    %% RefObj
    refVertexObj                          =geomDocu.CreateReferenceFromItem(VertexObj );
    refVertexTable.refObj                 =refVertexObj                 ;
    refVertexTable.Id                     =refVertexObj.GetId           ;    
    refVertexTable.IdentifierName         ={refVertexObj.GetIdentifier} ;
end