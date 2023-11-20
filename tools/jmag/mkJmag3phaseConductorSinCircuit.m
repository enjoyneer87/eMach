function mkJmag3phaseConductorSinCircuit(app)
Model=app.GetCurrentModel;
Study=app.GetCurrentStudy;
currentCircuit=Study.GetCircuit;
if ~currentCircuit.IsValid
Study.CreateCircuit()
Study.GetCircuit().CreateComponent("3PhaseCurrentSource", "CS1")
Study.GetCircuit().CreateInstance("CS1", -29, 0)
Study.GetCircuit().CreateComponent("WindingThreePhaseConductor", "Winding Three Phase Conductor1")
Study.GetCircuit().CreateInstance("Winding Three Phase Conductor1", -25, -1)
Study.GetCircuit().CreateComponent("Ground", "Ground")
Study.GetCircuit().CreateInstance("Ground", -23, 0)
else 
    disp('This Study already has circuit.')
end