function mkJMAGProbeGraphObj(app,ModelName,ProbeNameNPoint,ProbeType,ProbeName)
ModelObj=app.GetModel(ModelName);
if ModelObj.IsValid
    NumStudies  = ModelObj.NumStudies;
    for StudyIndex=1:NumStudies
    tempStudyObj=ModelObj.GetStudy(StudyIndex-1);
    StudyName=tempStudyObj.GetName;
    if ~tempStudyObj.GetProbe(ProbeName).IsValid
        tempObj=tempStudyObj.CreateProbe([StudyName,ProbeName]);
    end
    tempObj.SetResultType(ProbeType, "")
    tempObj.SetResultCoordinate("Cylindrical")
    if contains(ProbeType,"CurrentDensity")
    tempObj.SetComponent("Z")
    else
    tempObj.SetComponent("All")
    end
    tempObj.SetLocationCoordinate("Global Rectangular")
    tempObj.SetProbeType(0)
    % Probe Point1
    ProbeXpoint=ProbeNameNPoint{1}{1};
    ProbeYpoint=ProbeNameNPoint{1}{2};
    ProbeZpoint=ProbeNameNPoint{1}{3};
    tempObj.SetLocation(0,ProbeXpoint, ProbeYpoint, ProbeZpoint)
    tempObj.RenamePoint(0, ProbeNameNPoint{1}{4})
    % add other
    for PointIndex=2:length(ProbeNameNPoint)
        ProbePointName  =ProbeNameNPoint{PointIndex}{4};
        ProbeXpoint=ProbeNameNPoint{PointIndex}{1};
        ProbeYpoint=ProbeNameNPoint{PointIndex}{2};
        ProbeZpoint=ProbeNameNPoint{PointIndex}{3};
        tempObj.AddLocation(ProbeXpoint, ProbeYpoint, ProbeZpoint,ProbePointName)
    end
    tempObj.SetUseElementValue(false)
    tempObj.SetMoveWithPart(true)
    end
end %% ModelLoop