function mkJmag3phaseCoilSinCircuit(app)
    Model=app.GetCurrentModel;
    Study=app.GetCurrentStudy;
    currentCircuit=Study.GetCircuit;
    if ~currentCircuit.IsValid
    Study.CreateCircuit()
    Study.GetCircuit().CreateComponent("3PhaseCurrentSource", "CS1")
    Study.GetCircuit().CreateInstance("CS1", -29, 0)
    Study.GetCircuit().GetComponent("CS1").SetValue("CommutatingSequence", 0)
    % Star Connection
    Study.GetCircuit().CreateSubCircuit("Star Connection", "Star Connection1", -25, -1)
    % Study.GetCircuit().CreateComponent("WindingThreePhaseCoil", "Winding Three Phase Coil1")
    % Study.GetCircuit().CreateInstance("Winding Three Phase Coil1", -25, -1)
    Study.GetCircuit().CreateComponent("Ground", "Ground")
    Study.GetCircuit().CreateInstance("Ground", -23, 0)
    else 
        disp('This Study already has circuit.')
        if currentCircuit.GetComponent("CS1").IsValid
        currentCircuit.GetComponent("CS1").SetValue("CommutatingSequence", 0)
        end
    end
end