function [Rint, slot_pitch, ToothWidth, Angle_Radian_ToothWidth, imp_Tooth_Width_Ratio] = calcImplicitToothWidthRatio(BackIronThickness, i_YtoT, p_Tooth_Tip_Depth, i_Stator_OD, i_Split_Ratio, p_Stator_Slots)
    % Stator Dimension
    Rint = (i_Stator_OD * i_Split_Ratio) / 2;

    slot_pitch = 360 / p_Stator_Slots; % [in degrees]
    slot_pitch_rad = deg2rad(slot_pitch);

    % Tooth Width Calculation
    ToothWidth = BackIronThickness / i_YtoT;
    
    % Radius
    Radius_ToothWidth = Rint + p_Tooth_Tip_Depth - 0.05;
    
    % Angle
    Angle_Radian_ToothWidth = ToothWidth / Radius_ToothWidth;
    
    imp_Tooth_Width_Ratio = Angle_Radian_ToothWidth / slot_pitch_rad;
end
