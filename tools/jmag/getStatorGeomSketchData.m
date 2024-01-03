function AssemObjStruct=getStatorGeomSketchData(geomApp,AssembleName)
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
    % geomApp=app.CreateGeometryEditor(0);
    geomApp.GetDocument().GetAssembly().GetItem(AssembleName).OpenSketch();
    geomView=geomApp.View();
    geomView.SetSelectionFilter(int32(3+4+8))
    AssemObjStruct=getSkecthDataTableFromCurrentSelection(geomApp);
    
    geomApp.GetDocument().GetAssembly().GetItem(AssembleName).CloseSketch();

end