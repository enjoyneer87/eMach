function [Rint, slot_pitch, MidToothWidth, Angle_Radian_ToothWidth, Ratio_SlotWidth] = calcImplicitSlotWidthRatio(statorDepth, i_YtoT, p_Tooth_Tip_Depth, i_Stator_OD, i_Split_Ratio, p_Stator_Slots)
    % Stator Dimension
    Rint = (i_Stator_OD * i_Split_Ratio) / 2;

    slot_pitch = 360 / p_Stator_Slots; % [in degrees]
    slot_pitch_rad = deg2rad(slot_pitch);

    % Radius for Tooth Width Calculation
    % BottomToothWidth
    Radius_BottomToothWidth = Rint + p_Tooth_Tip_Depth - 0.05;

    % TopToothWidth
    Radius_TopToothWidth = i_Stator_OD/2-0.5-statorDepth.BackIronThickness;

    % MidToothWidth
    SlotRegionDepth=Radius_TopToothWidth-Radius_BottomToothWidth ;
    Radius_MidToothWidth = Radius_TopToothWidth-SlotRegionDepth/2;

    MidToothWidth = statorDepth.BackIronThickness / i_YtoT;

    % Radius_ToothWidth = Rint + p_Tooth_Tip_Depth - 0.05;
    
    % Angle
    Angle_Radian_ToothWidth = MidToothWidth / Radius_MidToothWidth;
    
    imp_Tooth_Width_Ratio = Angle_Radian_ToothWidth / slot_pitch_rad;
    Ratio_SlotWidth = (1-imp_Tooth_Width_Ratio);
end
