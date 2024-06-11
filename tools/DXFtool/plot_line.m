function h = plot_line(line,col)
% plot lines: (Xi,Yi,Xj,Yj) start and end points 
    
    Xi = line(1);
    Yi = line(2);
    Xj = line(3);
    Yj = line(4);

    h = plot([Xi Xj],[Yi Yj],'color',col);
    
end
