function RphActive=devsetFEMCoilTurnNRph(app,SeriesturnInSlot,ParallelPath)

resitivitityJMAG=1.673e-08;  % rho

NumModels=app.NumModels;
for ModelIndex=1:NumModels
    ModelObj        =app.GetModel(ModelIndex-1);
    NumStudies      =ModelObj.NumStudies;
    for StudyIndex=1:NumStudies
        PartStruct       = getJMAGDesignerPartStruct(app);
        PartStructByType = convertJmagPartStructByType(PartStruct);
        singleConductorArea=uniquetol(PartStructByType.SlotTable.Area,1e-5);
        
        equationStruct=getJmagDesignerEquationStruct(app);
        BoolStackLength=contains({equationStruct.Name},'length','IgnoreCase',true);
        stackLength=equationStruct(BoolStackLength).object.GetValue;
        LengthSlot=stackLength*2;
        BooclSPole=contains({equationStruct.Name},'POLES');
        NumPole=equationStruct(BooclSPole).object.GetValue;
        NumSlot=equationStruct(contains({equationStruct.Name},'SLOTS')).object.GetValue;

        NSPP        =calcNSPP(NumSlot,NumPole);
        N_serial    =SeriesturnInSlot*NSPP*(NumPole/2)/ParallelPath;   % [TBC]
        TotalLengthofPhaseInSeries      = mm2m(LengthSlot)*N_serial;  % in [m]
        ResistanceJmag4Turn             = resitivity2Resistance(TotalLengthofPhaseInSeries,...
        mmsq2msq(singleConductorArea), resitivitityJMAG);
        %[TBC]
        for ParallelIndex=2:ParallelPath
            if ParallelIndex>1
            refResistance=ResistanceJmag4Turn;
            RphActive    = ParallelResistance(refResistance,ResistanceJmag4Turn);
            end
        end
        isConductor=0;
        curStudyObj=ModelObj.GetStudy(StudyIndex-1);       
        mkDesignerEquation('SeriesturnInSlot',num2str(SeriesturnInSlot),curStudyObj)
        mkDesignerEquation('ParallelPath',num2str(ParallelPath),curStudyObj)
        mkDesignerEquation('EffectiveTurnN',"SeriesturnInSlot/ParallelPath",curStudyObj,'equation')
        mkDesignerEquation('ActiveResistance',num2str(RphActive),curStudyObj)
        % Coil Setting
        app.SetCurrentStudy(curStudyObj.GetName)
        curCircuitObj=curStudyObj.GetCircuit();
        curStarCnnctObj=curCircuitObj.GetSubCircuit("Star Connection1");
        NumCoilComponent=curStarCnnctObj.NumComponentsByType('Coil');
        for CompIndex=1:NumCoilComponent
            CoilCompObj=curStarCnnctObj.GetComponentByType('Coil',CompIndex-1);
            % set Turn
            % set Rph
            CoilCompObj.SetValue("Turn", "EffectiveTurnN")
            CoilCompObj.SetValue("Resistance", "ActiveResistance")
            % CoilCompObj.GetPropertyTable
        end
    end
end
% 
% 
% 
% % mcad=callMCAD
% 
% MotorCADGeo=tempDefMCADMachineData4Scaling(mcad)
% CoilWindingInfo=defCoilWindingInfoStruct(MotorCADGeo) 
% resitivitityJMAG=1.673e-08;  % rho
% 
% SingleCoilAreaJMAGInSqm= mmsq2msq(CoilWindingInfo.Area4Resistance);
% N_serial    =CoilWindingInfo.N_serial;
% N_parallel  =CoilWindingInfo.N_parallel;
% 
% TotalLengthofPhaseInSeries      = mm2m(LengthSlot)*N_serial;  % in [m]
% ResistanceJmag4Turn             = resitivity2Resistance(TotalLengthofPhaseInSeries,...
% SingleCoilAreaJMAGInSqm, resitivitityJMAG);
% for 
% RphaseActiveMCADWithPara        = ParallelResistance(ResistanceJmag4Turn,ResistanceJmag4Turn) 
