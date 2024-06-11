function [X,Y]=PosArc(arc)     
    x = arc(1);
    y = arc(2);
    r = arc(3);
    a1 = arc(4);
    a2 = arc(5);

    if a2<a1
        a2 = a2 + 360;
    end
    div=2000;
    theta = deg2rad(linspace(a1,a2,div));
    X = x + r*cos(theta);
    Y = y + r*sin(theta);

end