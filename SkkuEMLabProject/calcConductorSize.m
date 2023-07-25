function settedConductorData=calcConductorSize(settedConductorData)    
    %%Input Data define(%)      
    FillFactor                  = settedConductorData.FillFactor   ;
    Turn                        = settedConductorData.Turn         ;
    % parallelTurn                = settedConductorData.parallelTurn ;
    
    ins_Thick                   = settedConductorData.ins_Thick ;                            % 도체 절연체 두께
    Liner_Thick                 = settedConductorData.Liner_Thick ;                          % 절연지 두께
    % Copper_Depth                = settedConductorData.Copper_Depth ;                         % 슬롯 몇적의 몇%가 conductor로 채워지는지
    Conductor_Separation        = settedConductorData.Conductor_Separation ;                 % 도체사이 거리     
    Area_slot                   = settedConductorData.Area_slot ;
    slot_width                  = settedConductorData.slot_width ;
    % slot_depth                  = settedConductorData.slot_depth ;
    
    %% Compute Conductor Size
    area_slot = str2double(Area_slot);
    effective_slot_area = area_slot*(FillFactor/100);                                         %유효면적
    
    % new_slot_Depth = area_slot/slot_width                                                   %실제 슬롯 길이
    Turn_per_area = effective_slot_area/Turn;                                                 %한턴당 면적(나동기준)
    settedConductorData.effective_slot_width = slot_width - Liner_Thick*2 - ins_Thick*2 - Conductor_Separation*2; %한턴당 가로길이
    settedConductorData.effective_slot_Depth = Turn_per_area / settedConductorData.effective_slot_width;                              %한턴당 세로길이     
end