function CoilWindingInfo=defCoilWindingInfoStruct(MotorCADGeo)


    if nargin<1
    CoilWindingInfo.FillFactor          =60
    CoilWindingInfo.NumberofTurn        =25
    CoilWindingInfo.Pitch               =1
    CoilWindingInfo.N_parallel          =1
    CoilWindingInfo.SlotLayerNumber     =2
    CoilWindingInfo.PhaseNumber         =3
    CoilWindingInfo.SlotNumber          =6
    else
    % CoilWindingInfo.FillFactor          =MotorCADGeo.RequestedGrossSlotFillFactor
    CoilWindingInfo.PhaseNumber         =3
    CoilWindingInfo.SlotNumber          =MotorCADGeo.Slot_Number
    CoilWindingInfo.Pitch               =MotorCADGeo.MagThrow
    CoilWindingInfo.N_parallel          =MotorCADGeo.ParallelPaths  

        if double(MotorCADGeo.Armature_CoilStyle)==1
            CoilWindingInfo.SlotLayerNumber     =MotorCADGeo.WindingLayers
            CoilWindingInfo.NumberofTurn=CoilWindingInfo.SlotLayerNumber;
            N_turn=CoilWindingInfo.NumberofTurn;
            MotorCADGeo.Copper_Width
            MotorCADGeo.Copper_Height
             CoilWindingInfo.Area4Resistance=MotorCADGeo.ArmatureConductorCSA
        elseif double(MachineData.Armature_CoilStyle)==0
            CoilWindingInfo.FillFactor          =MotorCADGeo.GrossSlotFillFactor
            CoilWindingInfo.NumberofTurn        =MotorCADGeo.MagTurnsConductor
            N_turn=CoilWindingInfo.NumberofTurn;
            CoilWindingInfo.Area4Resistance                           =MachineData.ArmatureTurnCSA;
    
        end
    end

    %% Fill Factor
    % NetSlotFillFactor
    % Slot_Fill_(Slot_Area)
    % CoilWindingInfo.FillFactor=MachineData.GrossSlotFillFactor % Copper Slot Fill
    Kl=1;
    CoilWindingInfo.Kl=Kl;
    
    N_Coil=CoilWindingInfo.SlotNumber/CoilWindingInfo.PhaseNumber/2*CoilWindingInfo.SlotLayerNumber
    N_parallel=CoilWindingInfo.N_parallel
    N_serial=N_Coil/N_parallel;
    pitch=CoilWindingInfo.Pitch;
    
    CoilWindingInfo.N_serial               =N_serial;
    CoilWindingInfo.N_Coil                 =N_Coil;
    CoilWindingInfo.NumberofTurnPerPhase   =N_turn*N_Coil;
end