function R_phaseJMAG10t2para=devJmagPhaseResistanceFromWindingSet(CoilWindingInfo,app)
    resitivitityJMAG=1.4969e-08;

    sigmaJMAG        =1/resitivitityJMAG                ;
    N_turn           =  CoilWindingInfo.NumberofTurn    ;             
    N_serial         =  CoilWindingInfo.N_serial        ;             
    N_parallel       =  CoilWindingInfo.N_parallel      ;               
    kl               =  CoilWindingInfo.Kl              ;
    SlotNumber       =  CoilWindingInfo.SlotNumber      ;
    %% PartStruct
    PartStruct=getJMAGDesignerPartStruct(app);
    Name2="Conductor";
    isInsulation=contains({PartStruct.Name},Name2);
    InsulationStruct=PartStruct(isInsulation);
    InsulationStruct=getEdgeVertexIdwithXYZCheck(InsulationStruct,app);
    
    if length(InsulationStruct)==SlotNumber
        isSlotDivided=0;
    else
        isSlotDivided=1;
    end
    %% calc LengthSlot
    % propertiesTableWithValue=getJMagStudyProperties(app)
    Study           =app.GetCurrentStudy;
    StudyProperties =Study.GetStudyProperties();
    LengthStack=StudyProperties.GetValue('ModelThickness');
    % stackLengthIndex=contains(propertiesTableWithValue.propertiesName,'ModelThickness')
    % stackLengthProperties=propertiesTableWithValue(stackLengthIndex,:)
    % LengthStack =stackLengthProperties.("PropertiesValue(KeyValue)"){:}
    LengthSlot  =LengthStack*2;

    %% Calc Length of End Winding
    LengthEnd=calcJMAGEndWindingLength(InsulationStruct,CoilWindingInfo);
    % Single Wire Length
    L_phase=LengthSlot+LengthEnd;
    % 상당 직렬턴수
    NumberSeriesCoils=CoilWindingInfo.NumberofTurn*N_serial;  % 상당 직렬턴수
    % 상당 직렬 코일의 유효 길이
    TotalLengthofPhaseInSeries=L_phase*NumberSeriesCoils;  % in [m]

    % 총길이
    TotalLengthofPhase=L_phase*CoilWindingInfo.NumberofTurn*CoilWindingInfo.N_Coil;

    %% Area (Wedge 제외)
    if isSlotDivided==1
    JMAGSlotArea                    =uniquetol([InsulationStruct.Area])*2                          ;
    else
    JMAGSlotArea                    =uniquetol([InsulationStruct.Area])                           ;    
    end
    JMAGCopperArea                  =JMAGSlotArea*CoilWindingInfo.FillFactor        ;
    SingleCoilAreaJMAGInSqmm        =JMAGCopperArea/CoilWindingInfo.NumberofTurn    ;
    SingleCoilAreaJMAGInSqm         =sqmm2sqm(SingleCoilAreaJMAGInSqmm)/CoilWindingInfo.SlotLayerNumber;


    %% Calculation

    R_phaseJMAG10t2para = devCalcRphase(sigmaJMAG, mm2m(L_phase),kl,N_turn,SingleCoilAreaJMAGInSqm,N_serial,N_parallel);

end