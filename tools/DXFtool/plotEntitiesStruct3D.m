function plotEntitiesStruct3D(dxf)

    % getting plot started
    hold on
    axis equal
    view(3); % 3D view
    % axis off
    
    dxf.ne = length(dxf.entities);
    % plot all entities
    for i = 1:length(dxf.entities)
        
        % get colors
        line_col = color_code(dxf.entities(i).color);
        
        if (i < dxf.ne) && strcmp(dxf.entities(i+1).name, 'HATCH')
            hatch_col = color_code(dxf.entities(i+1).color);
        else
            hatch_col = 'none';
        end
        
        switch dxf.entities(i).name
            case 'POINT'
                dxf.entities(i).handle = plot_point3D(dxf.entities(i).point, line_col);
            case 'LINE'
                dxf.entities(i).handle = plot_line3D(dxf.entities(i).line, line_col);
            case 'LWPOLYLINE'
                dxf.entities(i).handle = plot_poly3D(dxf.entities(i).poly, line_col, hatch_col, dxf.entities(i).closed);
            case 'CIRCLE'
                dxf.entities(i).handle = plot_circle3D(dxf.entities(i).circle, dxf.divisions, line_col);
            case 'ARC'
                dxf.entities(i).handle = plot_arc3D(dxf.entities(i).arc, dxf.divisions, line_col);
            case 'ELLIPSE'
                dxf.entities(i).handle = plot_ellipse3D(dxf.entities(i).ellipse, dxf.divisions, line_col, hatch_col, dxf.entities(i).closed);
            case 'SPLINE'
                dxf.entities(i).handle = plot_spline3D(dxf.entities(i).spline, line_col);
        end

    end

end

function h = plot_poly3D(poly, col, col2, isclosed)
    % plot polygons incl. bulges by vertices (X, Y, Z)
    
    % Add Z coordinate if not present
    if size(poly, 2) == 2
        poly(:, 3) = 0; % Set Z to 0 for all points
    end

    if isclosed == 1
        h = patch('faces', 1:length(poly), 'vertices', poly, 'edgecolor', col, 'facecolor', col2);
    else % plot open polygon
        h = plot3(poly(:,1), poly(:,2), poly(:,3), 'color', col);
    end
end

function h = plot_circle3D(circle, div, col)
    % plot circles: (X Center, Y Center, Z Center, Radius)
    
    x = circle(1);
    y = circle(2);
    z = circle(3);
    r = circle(4);

    theta = linspace(0, 2*pi, div);
    X = x + r * cos(theta);
    Y = y + r * sin(theta);
    Z = z * ones(size(X));

    h = plot3(X, Y, Z, '-', 'color', col);

end

function h = plot_arc3D(arc, div, col)
    % plot arcs: (X Center, Y Center, Z Center, Radius, Start angle, End angle)
    
    x = arc(1);
    y = arc(2);
    z = arc(3);
    r = arc(4);
    a1 = arc(5);
    a2 = arc(6);

    if a2 < a1
        a2 = a2 + 360;
    end

    theta = deg2rad(linspace(a1, a2, div));
    X = x + r * cos(theta);
    Y = y + r * sin(theta);
    Z = z * ones(size(X));

    h = plot3(X, Y, Z, '-', 'color', col);

end

function h = plot_ellipse3D(ellipse, div, line_col, hatch_col, isclosed)
    % plot ellipses: (X center, Y center, Z center, X end, Y end, Z end, ratio, start, end)

    Cx = ellipse(1);  % center
    Cy = ellipse(2);
    Cz = ellipse(3);
    Ex = -ellipse(4); % X value of endpoint of major axis, relative to the center
    Ey = -ellipse(5); % Y value of endpoint of major axis, relative to the center
    Ez = -ellipse(6); % Z value of endpoint of major axis, relative to the center
    R  = ellipse(7);  % Ratio of minor axis to major axis

    u1 = ellipse(8);  % Start parameter of u (this value is 0.0 for a full ellipse)
    u2 = ellipse(9);  % End parameter of u (this value is 2pi for a full ellipse)

    E = [Ex Ey Ez]';
    a = -norm(E);
    b = R * a;

    % rotation of the ellipse
    theta = atan2(Ey, Ex);
    Rm = rotation(theta);

    % sweep
    u = linspace(u2, u1, div);
    for j = 1:div

        P(1) = a * cos(u(j));
        P(2) = b * sin(u(j));
        P(3) = 0; % Z component for the ellipse is constant

        Pr = Rm * P';

        X(j) = Cx + Pr(1);
        Y(j) = Cy + Pr(2);
        Z(j) = Cz + Pr(3);

    end
    
    if isclosed
        h = patch('faces', 1:length(X), 'vertices', [X' Y' Z'], 'edgecolor', line_col, 'facecolor', hatch_col);
    else
        h = plot3(X, Y, Z, '-', 'color', line_col);
    end
end

function h = plot_point3D(point, col)
    % plot points

    X = point(1);
    Y = point(2);
    Z = point(3);
    h = plot3(X, Y, Z, 'k', 'markerfacecolor', col);

end

function h = plot_line3D(line, col)
    % plot lines: (Xi, Yi, Zi, Xj, Yj, Zj) start and end points 
    
    Xi = line(1);
    Yi = line(2);
    Zi = line(3);
    Xj = line(4);
    Yj = line(5);
    Zj = line(6);

    h = plot3([Xi Xj], [Yi Yj], [Zi Zj], 'color', col);
    
end

function h = plot_spline3D(sp, col)
    % plot splines as piecewise linear poly line (very crude) 

    poly = [sp.X sp.Y sp.Z];
    h = plot_poly3D(poly, col, '', 0);
    
end

function R = rotation(theta)
    % 2D rotation matrix
    R = [cos(theta) -sin(theta); sin(theta) cos(theta)];
end