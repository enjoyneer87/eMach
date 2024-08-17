function setRPBoundaryCondition(studyObj, RotorOnePoleAngle,StatorEdgeXposition)
    % dev Temp
     % studyObj =curStudyObj;
    % studyObj.GetConditionTypes
    % NumConditions=studyObj.NumConditions;
    if studyObj.GetCondition('RPBoundary').IsValid
    RPBoundaryOBJ=studyObj.GetCondition('RPBoundary');
    else
    RPBoundaryOBJ=studyObj.CreateCondition('RotationPeriodicBoundary','RPBoundary');
    end
    
    RPBoundaryOBJ.SetValue("BoundaryType", 1)  % 0 periodic 1: anti-periodic
    RPBoundaryOBJ.SetValue('Angle',RotorOnePoleAngle)
    %% Condition Object Selection Get
    ConSel = RPBoundaryOBJ.GetSelection();
    ConSel.IsValid
    ConSel.Clear;
    ConSel.NumEdges
    %% Select Edge By Position
    ConSel.SelectEdgeByPosition(StatorEdgeXposition,0,0);
    RPBoundaryOBJ.AddSelected(ConSel);
end