function LengthEnd=calcJMAGEndWindingLength(InsulationStruct,CoilWindingInfo)
   
    % LengthHori
    SlotPartcentroidRadius          =InsulationStruct.CentroidR;
    LengthHori                      =(2*pi*SlotPartcentroidRadius/CoilWindingInfo.SlotNumber)*CoilWindingInfo.Pitch*2;
    % SlotLwind
    AreaSlot                        =InsulationStruct.Area;
    SlotradiusMin                   =InsulationStruct(1).VertexMinRPos;
    SlotradiusMax                   =InsulationStruct(1).VertexMaxRPos;
    SlotLwind                       =AreaSlot/(2*(SlotradiusMax-SlotradiusMin));
    % Lvertical
    % NumberOfCoils=N_turn*N_serial
    NumberOfCoils                   =CoilWindingInfo.N_Coil;
    
    LegnthVertical                  =SlotLwind*NumberOfCoils*2;
    % LegnthVertical=SlotLwind*8*2
    % LengthEnd
    % LengthEnd=NumberOfCoils*(LengthHori+LegnthVertical);
    
    LengthEnd                       =(LengthHori+LegnthVertical);

end