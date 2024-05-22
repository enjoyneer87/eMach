function distanceFromCenter=getDistanceFromZero(refObj,geomApp)

%% check App or Geometry Editor
    AppDir=geomApp.GetAppDir;
    AppDirStr=split(AppDir,'/');
    if ~strcmp(AppDirStr{end},'Modeller')
        geomApp=geomApp.CreateGeometryEditor(0);
        % geomApp.Show
    end

geomDocu=geomApp.GetDocument;
geomDocuMeasureManager         =geomDocu.GetMeasureManager;

%% get Distance
distanceFromCenter=     geomDocuMeasureManager.MeasureDistanceFrom(0,0,0,refObj);


end
