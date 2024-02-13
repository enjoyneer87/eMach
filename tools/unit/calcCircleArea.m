function area = calcCircleArea(diameter1, diameter2)
    % Calculate the area of a circle or a ring (donut shape).
    %
    % Parameters:
    % diameter1: Diameter of the first circle (mm)
    % diameter2: Diameter of the second circle (mm), optional. Default is empty.
    %
    % Returns:
    % area: Area of the circle or the ring (mm²)

    % Calculate the area of the first circle
    area1 = pi * (diameter1 / 2)^2;

    if nargin == 2 && ~isempty(diameter2)
        % If the second diameter is provided, calculate the area of the second circle
        area2 = pi * (diameter2 / 2)^2;
        % Calculate the area of the ring (donut shape)
        area = area1 - area2;
    else
        % If only one diameter is provided, return the area of the single circle
        area = area1;
    end
end
