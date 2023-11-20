function sel=mkSelectionObj(app,~)
    geomApp=app.CreateGeometryEditor(0);
    geomView=geomApp.View();
    geomDocu=geomApp.GetDocument();
    xstart=0;
    ystart=0;
    zstart=0;
    xMax=400;
    yMax=400;
    zMax=400;
    geomView.SelectByCircleWorldPos(xstart, ystart,zstart, xMax, yMax, zMax, 0);
    % sel=geomDocu.GetSelection;
    sel=geomDocu.GetSelection;
    if nargin<2
    sel.Clear;
    end
    % geomApp.GetDocument().GetAssembly().GetItem().OpenSketch();
    % geomView.SetSelectionFilter('Region')
end