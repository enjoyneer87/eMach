function CoilWindingInfo=defCoilWindingInfoStruct(MotorCADGeo)
%% dev
% MotorCADGeo=MachineData

%%
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
    PhaseNumber         =3;
    SlotNumber          =MotorCADGeo.Slot_Number;
    Pole                =MotorCADGeo.Pole_Number;
    Pitch               =MotorCADGeo.MagThrow;
    N_parallel          =MotorCADGeo.ParallelPaths  ;

        if double(MotorCADGeo.Armature_CoilStyle)==1
            SlotLayerNumber                     =MotorCADGeo.WindingLayers;
            CoilWindingInfo.NumberofTurn        =SlotLayerNumber;
            N_turn=CoilWindingInfo.NumberofTurn;

            CoilWindingInfo.SlotLayerNumber     =SlotLayerNumber;
            CoilWindingInfo.Copper_Width        =MotorCADGeo.Copper_Width;
            CoilWindingInfo.Copper_Height       =MotorCADGeo.Copper_Height;
            CoilWindingInfo.Area4Resistance=MotorCADGeo.ArmatureConductorCSA;
        elseif double(MachineData.Armature_CoilStyle)==0
            CoilWindingInfo.FillFactor          =MotorCADGeo.GrossSlotFillFactor
            CoilWindingInfo.NumberofTurn        =MotorCADGeo.MagTurnsConductor
            N_turn=CoilWindingInfo.NumberofTurn;
            CoilWindingInfo.Area4Resistance    =MachineData.ArmatureTurnCSA;
        end
    end

    %% Fill Factor
    % NetSlotFillFactor
    % Slot_Fill_(Slot_Area)
    % CoilWindingInfo.FillFactor=MachineData.GrossSlotFillFactor % Copper Slot Fill
    Kl=1;
    CoilWindingInfo.Kl=Kl;
    N_Coil             =calcNumberCoil(SlotNumber,SlotLayerNumber,PhaseNumber);
    N_serial           =N_Coil/N_parallel;
    NSPP               =calcNSPP(SlotNumber,Pole);
    %% 2 Struct
    CoilWindingInfo.PhaseNumber            =PhaseNumber ;
    CoilWindingInfo.SlotNumber             =SlotNumber  ;
    CoilWindingInfo.Pitch                  =Pitch       ;
    CoilWindingInfo.N_parallel             =N_parallel  ;
    CoilWindingInfo.NSPP                   =NSPP;
    CoilWindingInfo.N_serial               =N_serial;       %  The number of turns per phase in each parallel path 상당직렬턴수 Coil 같지 
    %Armature Turns per Phase 과 동일하지 싶은데 
    CoilWindingInfo.tempNumberofTurnPerPhase   =N_turn*N_Coil;  % TC
    CoilWindingInfo.N_Coil                 =N_Coil;         % N_serial * N_parallel
    CoilWindingInfo.tempActualTurnPerSlot      =N_serial/NSPP/(Pole/2) ;
    CoilWindingInfo.Total_Coil             =CoilWindingInfo.PhaseNumber*N_Coil;
end