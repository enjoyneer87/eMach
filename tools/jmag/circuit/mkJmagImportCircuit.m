function mkJmagImportCircuit(app,circuitPath)
    
    Model=app.GetCurrentModel;
    Study=app.GetCurrentStudy;
    currentCircuit=Study.GetCircuit;

    if nargin<2
    circuitPath='Z:/Thesis/00_Theory_Prof/JFTZIP/JFT047FeedbackControl/JFT047FeedbackControl/IPM_PWM_FEMConductor.jcir';
    end
    
    if ~currentCircuit.IsValid
    Study.LoadCircuit(circuitPath)
    elseif currentCircuit.NumComponents==0 
        Study.LoadCircuit(circuitPath)
     
    else
        disp('This Study already has circuit.')
    end

end