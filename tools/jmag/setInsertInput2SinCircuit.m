function setInsertInput2SinCircuit(app,InputCurrentData)

%% Ipk와 phaseAdvace, freE를 별도로 넣으셔야됩니다.

    Study=app.GetCurrentStudy;
    currentCircuit=Study.GetCircuit;
    if currentCircuit.IsValid
        SinCS1Component=currentCircuit.GetComponent("CS1");
    else
        mkJmag3phaseConductorSinCircuit(app);
    end
    if SinCS1Component.IsValid
        if nargin<2
            SinCS1Component.SetValue("Amplitude", "Ipk");
            SinCS1Component.SetValue("Frequency", "freE");
            SinCS1Component.SetValue("PhaseU", "phaseAdvance");       
        else
            SinCS1Component.SetValue("Amplitude", InputCurrentData.Current             );
            SinCS1Component.SetValue("Frequency", InputCurrentData.freE                );
            SinCS1Component.SetValue("PhaseU",    InputCurrentData.phaseAdvance        );       
        end
    end
end