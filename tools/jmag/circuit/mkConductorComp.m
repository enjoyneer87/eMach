function [aComponent,aInstance]=mkConductorComp(name,app,position)
% Model         =app.GetCurrentModel;
curStudyObj   =app.GetCurrentStudy;
curCircuitObj =app.GetCurrentStudy.GetCircuit;
if nargin<3
position=[0,0]
end
%%
aComponent =curCircuitObj.CreateComponent("FEMConductor", name);
aInstance  =curStudyObj.GetCircuit().CreateInstance(name, position(1),position(2));
end