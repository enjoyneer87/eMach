% Obj
function vertexTable=getVertexTable(StartVertex,app)
% ItemObj
% Obj Handle
% Name
% Type
% X Y Z Position [CC] & R theta
StartVertexTable    =getPositionTableFromPostionObj( StartVertex );

%% RefObj
% refObj Handle
%  Id
%  IdentifierName
refStartVertexTable=getRefVertexTableFromItemObj(StartVertex,app);

%%
vertexTable=[StartVertexTable refStartVertexTable];
end