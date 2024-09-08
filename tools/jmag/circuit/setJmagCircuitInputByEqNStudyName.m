function setJmagCircuitInputByEqNStudyName(app,RMSCurrent,ParallelNumber)
NumModels=app.NumModels;
for ModelIndex=1:NumModels
    ModelObj=app.GetModel(ModelIndex-1);
    NumStudies=ModelObj.NumStudies;
    for StudyIndex=1:NumStudies
        curStudyObj=ModelObj.GetStudy(StudyIndex-1);
        app.SetCurrentStudy(curStudyObj.GetName)
        InputCurrentData.ParallelNumber=ParallelNumber;
        InputCurrentData.Current=RMSCurrent*sqrt(2);
        InputCurrentData.freqE='FreqE';
        InputCurrentData.phaseAdvance='MCADPhaseAdvance';
        % No Load & Load    
        curStudyName=curStudyObj.GetName;
        if contains(curStudyName,'No') || contains(curStudyName,'_Load')
        setInsertInput2SinCircuit(app,InputCurrentData)
        % PWM
        elseif contains(curStudyName,'PWM')
        loadJMAG_PWMInput(app)
        curStudyObj.GetCircuit().GetComponent("theta_m").SetLink("Rotation")
        end
    end
end

