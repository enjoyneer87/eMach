function NewConductorData=calcConductorSize(conductorData)    
    %%Input Data define(%)     
    tic
    WindingLayers               = conductorData.WindingLayers;
    Insulation_Thickness        = conductorData.Insulation_Thickness;                           % 도체 절연체 두께
    Liner_Thickness             = conductorData.Liner_Thickness;                                % 절연지 두께
    ConductorSeparation         = conductorData.ConductorSeparation;                            % 도체사이 거리     
    Area_Slot                   = str2double(conductorData.Area_Slot);
    Area_Winding_With_Liner     = str2double(conductorData.Area_Winding_With_Liner);
    Slot_Width                  = conductorData.Slot_Width;
    % Slot_Depth                  = settedConductorData.Slot_Depth;
    Winding_Depth               = conductorData.Winding_Depth;
    FillFactor                  = conductorData.temp_fillfactor;
    toc
    %% Data 삭제
    conductorData         = rmfield(conductorData,'temp_fillfactor');
    effective_FillFactor        = Area_Slot*FillFactor/Area_Winding_With_Liner;
    
    %% 알고리즘 Compute Conductor Size
    area_slot = Area_Winding_With_Liner;
    effective_slot_area = area_slot*(effective_FillFactor/100);                                         % 유효면적
    Turn_per_area = effective_slot_area/WindingLayers;                                                 % 한 턴 당 면적 (나동 기준)
    NewConductorData.Copper_Width = Slot_Width - Liner_Thickness*2 - Insulation_Thickness*2 - ConductorSeparation*2;  % 한 턴 당 너비 (회전방향)
    NewConductorData.Copper_Height = Turn_per_area / conductorData.Copper_Width;  % 한턴당 세로길이
    
    %%
    if NewConductorData.Copper_Height>(Winding_Depth-Liner_Thickness-10*2*Insulation_Thickness-11*ConductorSeparation)/10
        temp_Copper_Height=NewConductorData.Copper_Height;
        NewConductorData.Copper_Height = (Winding_Depth-Liner_Thickness-10*2*Insulation_Thickness-11*ConductorSeparation)/10;
    end
end