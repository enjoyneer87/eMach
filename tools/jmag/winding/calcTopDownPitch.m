function TotalTable=calcTopDownPitch(TotalTable,NumSlots)
    %%init
    GoSlot          =TotalTable.GoSlot;
    ReturnSlot      =TotalTable.ReturnSlot;
    pitch={0};
    %% Calc DownPitch
    for coilIndex=1:height(TotalTable)-1
        if TotalTable.PhaseNumber(coilIndex)==TotalTable.PhaseNumber(coilIndex+1)
        [direction, pitch{coilIndex+1,1}] = calcPitchwithDirection(str2num(ReturnSlot{coilIndex}),str2num(GoSlot{coilIndex+1}), NumSlots);
        end
    end
    %% add Table
    TotalTable.DownPitch=pitch;
end
