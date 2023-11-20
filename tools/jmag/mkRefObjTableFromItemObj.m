function refVertexTable=mkRefObjTableFromItemObj(VertexObj,app)

geomApp=app.CreateGeometryEditor(0);
geomDocu=geomApp.GetDocument;
refVertexTable=table();
%% RefObj
refVertexObj                          =geomDocu.CreateReferenceFromItem(VertexObj );
refVertexTable.refObj                 =refVertexObj                 ;
refVertexTable.Id                     =refVertexObj.GetId           ;    
refVertexTable.IdentifierName         ={refVertexObj.GetIdentifier} ;
end