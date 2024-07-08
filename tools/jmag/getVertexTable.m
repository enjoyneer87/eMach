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

%%
if nargin>1
refStartVertexTable=getRefVertexTableFromItemObj(StartVertex,app);
vertexTable=[StartVertexTable refStartVertexTable];
else
vertexTable=StartVertexTable;
end