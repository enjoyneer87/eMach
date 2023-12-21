function AssemObjStruct=getStatorGeomSketchData(app,AssembleName)
% Fields
% Name          (selection Class)
% ReferenceObj
% IdentifierName (ReferenceObj class)
% Id             (ReferenceObj class)
% Type           (selection Class)
if nargin<2
AssembleName='Stator';
end
%%
    geomApp=app.CreateGeometryEditor(0);
    geomApp.GetDocument().GetAssembly().GetItem(AssembleName).OpenSketch();
    % geomView.SetSelectionFilter('Region')
    AssemObjStruct=getSkecthDataTableFromCurrentSelection(app);
    
    geomApp.GetDocument().GetAssembly().GetItem(AssembleName).CloseSketch();

end