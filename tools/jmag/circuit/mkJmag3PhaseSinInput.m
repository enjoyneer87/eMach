function [compObj,InstanceObj]=mkJmag3PhaseSinInput(app,Position)
    %% Initial Obj
    curStudyObj   = app.GetCurrentStudy;
    curCircuitObj = app.GetCurrentStudy.GetCircuit;
    %% 
    if nargin<2
        Position=[0,0];
    end

%% Create Sin Input
    compObj=curCircuitObj.CreateComponent("3PhaseCurrentSource", "CS1");
    InstanceObj=curCircuitObj.CreateInstance("CS1", Position(1), Position(2));
end