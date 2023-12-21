function sel=mkSelectionObj(geomApp,~)
    %% Need to OpenSketch before excute This Function
    % geomApp=app.CreateGeometryEditor(0);
    AppDir=geomApp.GetAppDir;
    AppDirStr=split(AppDir,'/');
    if ~strcmp(AppDirStr{end},'Modeller')
     geomApp=geomApp.CreateGeometryEditor(0);
    end
    
    % geomApp.visible
    geomDocu=geomApp.GetDocument();
    sel=geomDocu.GetSelection;
    % sel.Add
    % 
    if nargin<2
    geomApp.Hide;
    sel.Clear;
    else
    geomView=geomApp.View();
    xstart=0;
    ystart=0;
    zstart=0;
    xMax=4*10e6;
    yMax=4*10e6;
    zMax=4*10e6;
    geomView.SelectByCircleWorldPos(xstart, ystart,zstart, xMax, yMax, zMax, 0);
    sel=geomDocu.GetSelection;
    end
    % geomApp.GetDocument().GetAssembly().GetItem().OpenSketch();
    % geomView.SetSelectionFilter('Region')
end