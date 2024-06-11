function plotEntitiesStruct(dxf)

            % getting plot started
            hold on
            axis equal
            %axis off
            
            dxf.ne=length(dxf.entities);
            % plot all entities
            for i = 1:length(dxf.entities)
                
                % get colors
                line_col = color_code(dxf.entities(i).color);
                
                if (i<dxf.ne) && strcmp(dxf.entities(i+1).name,'HATCH')
                    hatch_col = color_code(dxf.entities(i+1).color);
                else
                    hatch_col = 'none';
                end
                
                switch dxf.entities(i).name
                    case 'POINT'
                        dxf.entities(i).handle = plot_point(dxf.entities(i).point,line_col);
                    case 'LINE'
                        dxf.entities(i).handle = plot_line(dxf.entities(i).line,line_col);
                    case 'LWPOLYLINE'
                        dxf.entities(i).handle = plot_poly(dxf.entities(i).poly,line_col,hatch_col,dxf.entities(i).closed);
                    case 'CIRCLE'
                        dxf.entities(i).handle = plot_circle(dxf.entities(i).circle,dxf.divisions,line_col);
                    case 'ARC'
                        dxf.entities(i).handle = plot_arc(dxf.entities(i).arc,dxf.divisions,line_col);
                    case 'ELLIPSE'
                        dxf.entities(i).handle = plot_ellipse(dxf.entities(i).ellipse,dxf.divisions,line_col,hatch_col,dxf.entities(i).closed);
                    case 'SPLINE'
                        dxf.entities(i).handle = plot_spline(dxf.entities(i).spline,line_col);
                end

            end

        end
       




function h = plot_poly(poly,col,col2,isclosed)
% plot polygons incl. bulges by vertices (X,Y)

    if isclosed==1
        h = patch('faces',1:length(poly),'vertices',poly,'edgecolor',col,'facecolor',col2);
    else % plot open polygon
        h = plot(poly(:,1),poly(:,2),'color',col);
    end

end

function h = plot_circle(circle,div,col)
% plot circles: (X Center,Y Center,Radius)
    
    x = circle(1);
    y = circle(2);
    r = circle(3);

    theta = linspace(0,2*pi,div);
    X = x + r*cos(theta);
    Y = y + r*sin(theta);

    h = plot(X,Y,'-','color',col);

end

function h = plot_arc(arc,div,col)
% plot arcs: (X Center,Y Center,Radius,Start angle,End angle)
        
    x = arc(1);
    y = arc(2);
    r = arc(3);
    a1 = arc(4);
    a2 = arc(5);

    if a2<a1
        a2 = a2 + 360;
    end

    theta = deg2rad(linspace(a1,a2,div));
    X = x + r*cos(theta);
    Y = y + r*sin(theta);

    h = plot(X,Y,'-','color',col);

end

function h = plot_ellipse(ellipse,div,line_col,hatch_col,isclosed)
% plot ellipses: (% X center ,Y center, X end, Y end, ratio, start, end)
% https://www.autodesk.com/techpubs/autocad/acad2000/dxf/ellipse_command39s_parameter_option_dxf_06.htm

    Cx = ellipse(1);  % center
    Cy = ellipse(2);
    Ex = -ellipse(3); % X value of endpoint of major axis, relative to the center
    Ey = -ellipse(4); % Y value of endpoint of major axis, relative to the center
    R  = ellipse(5);  % Ratio of minor axis to major axis

    u1 = ellipse(6);  % Start parameter of u (this value is 0.0 for a full ellipse)
    u2 = ellipse(7);  % End parameter of u (this value is 2pi for a full ellipse)

    E = [Ex Ey]';
    a = -norm(E);
    b = R*a;

    % rotation of the ellipse
    theta = atan2(Ey,Ex);
    rad2deg(theta)
    R = rotation(theta);

    % sweep
    u = linspace(u2,u1,div);
    for j = 1:div

        P(1) = a*cos(u(j));
        P(2) = b*sin(u(j));

        Pr = R*P';

        X(j) = Cx + Pr(1);
        Y(j) = Cy + Pr(2);

    end

    
    if isclosed
        h = patch('faces',1:length(X),'vertices',[X' Y'],'edgecolor',line_col,'facecolor',hatch_col);
    else
        h = plot(X,Y,'-','color',line_col);
    end
    
end

function h = plot_point(point,col)
% plot points

    X = point(1);
    Y = point(2);
    h = plot(X,Y,'k','markerfacecolor',col);

end

function h = plot_line(line,col)
% plot lines: (Xi,Yi,Xj,Yj) start and end points 
    
    Xi = line(1);
    Yi = line(2);
    Xj = line(3);
    Yj = line(4);

    h = plot([Xi Xj],[Yi Yj],'color',col);
    
end

function h = plot_spline(sp,col)
% plot splines as piecewise linear poly line (very crude) 

    poly = [sp.X sp.Y];
    h = plot_poly(poly,col,'',0);
    
end