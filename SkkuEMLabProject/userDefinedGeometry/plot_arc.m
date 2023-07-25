function plot_arc(radius, start_angle, end_angle)
    theta = linspace(start_angle, end_angle, 100);
    x = radius * cos(theta);
    y = radius * sin(theta);
    plot(x, y);
    axis equal;
end
