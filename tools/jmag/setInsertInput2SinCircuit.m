function setInsertInput2SinCircuit(app,InputCurrentData)

%% Ipk와 phaseAdvace, freqE를 별도로 넣으셔야됩니다.

    StudyObj=app.GetCurrentStudy;
    StudyName=StudyObj.GetName;
    currentCircuit=StudyObj.GetCircuit;

%% InputData
    pole=InputCurrentData.pole;
    slot=InputCurrentData.slot;
    ParallelNumber=InputCurrentData.ParallelNumber;
    %% Circuit 입력이 존재하는지 확인 
    
    if currentCircuit.IsValid
        SinCS1Component=currentCircuit.GetComponent("CS1");
    elseif currentCircuit.NumComponents==0
        %[TC] 존재안하면 이 회로 기본적으로 입력
        jcirFilePath=mkJmag3phaseCoilSinCircuit(app);
        % jcirFilePath=mkJmag3phaseConductorSinCircuit(app);
        currentCircuit=StudyObj.GetCircuit;
        SinCS1Component=currentCircuit.GetComponent("CS1");
    end

    %% 무부하 부하 구분
    if contains(StudyName,'Noload','IgnoreCase',true)
        % SinCS1Component.delete
        currentCircuit.DeleteInstance("CS1", 0)

    elseif contains(StudyName,'load','IgnoreCase',true) && ~contains(StudyName,'Noload','IgnoreCase',true)
        %% 없으면 만들기~
        if ~SinCS1Component.IsValid
              % Input Circuit Component
              CoilList            =InputCurrentData.CoilList;
              % NumFEMConductor=currentCircuit.NumComponentsByType("FEMConductor");
              PhaseStruct         = mkConductorCircuit(pole,slot,ParallelNumber, CoilList, app, 70) ;                   
              ConductorXPosition  = PhaseStruct(2).StartPosition(3)          ;       
              xPosition           = ConductorXPosition-10                    ;
              ConductorYPosition  = PhaseStruct(2).StartPosition(4)          ;       
              InputPosition       =[xPosition,ConductorYPosition]                            ;
          %% mk Input Component
              [compObj,~]=mkJmag3PhaseSinInput(app,InputPosition);
              TerminalPositionList{1}=[InputPosition(1)+2,InputPosition(2)+2];
              TerminalPositionList{2}=[InputPosition(1)+2,InputPosition(2)];
              TerminalPositionList{3}=[InputPosition(1)+2,InputPosition(2)-2];   
           %% Connect each phase to Input
            for PhaseIndex=1:3 
              StartPosition=PhaseStruct(PhaseIndex).StartPosition;
              TerminalPosition=TerminalPositionList{PhaseIndex};
              currentCircuit.CreateWire(StartPosition(3)-2, StartPosition(4), TerminalPosition(1),StartPosition(4));
              currentCircuit.CreateWire(TerminalPosition(1),StartPosition(4), TerminalPosition(1),TerminalPosition(2));
            end
              SinCS1Component=compObj;
        end        
        %% Sin값 넣기
        if nargin<2
            SinCS1Component.SetValue("Amplitude", "Ipk");
            SinCS1Component.SetValue("Frequency", "freqE");
            SinCS1Component.SetValue("PhaseU", "phaseAdvance");     
            SinCS1Component.SetValue("CommutatingSequence", 0);
        else
            SinCS1Component.SetValue("Amplitude", InputCurrentData.Current             );
            SinCS1Component.SetValue("Frequency", InputCurrentData.freqE                );            
            SinCS1Component.SetValue("PhaseU",    "MCADPhaseAdvance"       );       
            SinCS1Component.SetValue("CommutatingSequence", 0);
        end
        
    end    
end