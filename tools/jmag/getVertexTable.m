% Obj
function vertexTable=getVertexTable(StartVertex,app)
% ItemObj
% Obj Handle
% Name
% Type
% X Y Position
StartVertexTable    =getPositionTableFromPostionObj( StartVertex );
%% RefObj
% refObj Handle
%  Id
%  IdentifierName
refStartVertexTable=getRefVertexTableFromItemObj(StartVertex,app);

%%
vertexTable=[StartVertexTable refStartVertexTable];
end