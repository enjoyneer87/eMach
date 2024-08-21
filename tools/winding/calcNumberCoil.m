function N_Coil=calcNumberCoil(SlotNumber,SlotLayerNumber,PhaseNumber)

    if nargin<3
        PhaseNumber=3;
    end
    N_Coil             =SlotNumber/PhaseNumber/2*SlotLayerNumber;

end