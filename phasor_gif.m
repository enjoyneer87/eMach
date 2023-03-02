for i=1:25000
    clf;
    quiver(0,0,xdq(1,3*i),0,'off')
    hold on
    quiver(0,0,0,xdq(2,3*i),'off')
    hold on
    quiver(0,0,xdq(1,3*i),xdq(2,3*i),'off')
    hold on
    drawnow limitrate

    % getframe(gcf); 
end