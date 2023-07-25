function distance = CalcSlotOpening(Rint, p_Tooth_Tip_Depth, slot_pitch, Angle_Radian_ToothWidth)
    % Example usage
    radius = Rint + p_Tooth_Tip_Depth;
    start_angle = 0;
    end_angle = slot_pitch * pi / 180 - Angle_Radian_ToothWidth;
    plot_arc(radius, start_angle, end_angle);

    arc_length = calculate_arc_length(radius, end_angle - start_angle);
    distance = calculate_distance(radius, end_angle - start_angle);
    % Calculate the coordinates of the two points on the arc
    x_start = radius * cos(start_angle);
    y_start = radius * sin(start_angle);
    x_end = radius * cos(end_angle);
    y_end = radius * sin(end_angle);
    % Plot a straight line representing the distance
    plot([x_start, x_end], [y_start, y_end], 'r--');
end
