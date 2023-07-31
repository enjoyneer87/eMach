function settedConductorData=calcConductorSize(settedConductorData)    
    %%Input Data define(%)      
    WindingLayers               = settedConductorData.WindingLayers;
    Insulation_Thickness        = settedConductorData.Insulation_Thickness;                            % 도체 절연체 두께
    Liner_Thickness             = settedConductorData.Liner_Thickness;                          % 절연지 두께
    ConductorSeparation         = settedConductorData.ConductorSeparation;                 % 도체사이 거리     
    Area_Slot                   = str2double(settedConductorData.Area_Slot);
    Area_Winding_With_Liner     = str2double(settedConductorData.Area_Winding_With_Liner);
    Slot_Width                  = settedConductorData.Slot_Width;
    % Slot_Depth                  = settedConductorData.Slot_Depth;
    Winding_Depth               = settedConductorData.Winding_Depth;

    FillFactor                  = settedConductorData.temp_fillfactor;
    effective_FillFactor        = Area_Slot*FillFactor/Area_Winding_With_Liner;
    
    %% Compute Conductor Size
    area_slot = Area_Winding_With_Liner;
    effective_slot_area = area_slot*(effective_FillFactor/100);                                         % 유효면적
    Turn_per_area = effective_slot_area/WindingLayers;                                                 % 한 턴 당 면적 (나동 기준)
    settedConductorData.Copper_Width = Slot_Width - Liner_Thickness*2 - Insulation_Thickness*2 - ConductorSeparation*2;  % 한 턴 당 너비 (회전방향)
    settedConductorData.Copper_Height = Turn_per_area / settedConductorData.Copper_Width;  % 한턴당 세로길이
    if settedConductorData.Copper_Height>(Winding_Depth-Liner_Thickness-10*2*Insulation_Thickness-11*ConductorSeparation)/10
        settedConductorData.Copper_Height = (Winding_Depth-Liner_Thickness-10*2*Insulation_Thickness-11*ConductorSeparation)/10;
    end
end