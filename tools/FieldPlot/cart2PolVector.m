function [Fr, Ftheta] = cart2PolVector(Fx, Fy, x, y)
    % Cartesian (x, y) 성분을 Polar (r, theta) 성분으로 변환
    % Fx, Fy: x, y 방향의 물리량 성분
    % x, y: 위치 좌표  % col
    sizeFx=size(Fx);
    sizeFy=size(Fy);
    sizex =size(x);
    sizey =size(y);

    if ~sizex==sizey
    error('x,y좌표가 안맞습니다')   
    elseif sizex(2)<sizex(1)  % 2가 더 커야됨 행배열
    x=x';
    y=y';
    sizex =size(x);
    sizey =size(y);
    end

    if ~sizex(2)==sizeFy(2)
    Fx=Fx';
    Fy=Fy';
    end
    
    % 반지름과 각도 계산
    r = sqrt(x.^2 + y.^2);
    theta = atan2(y, x);
    % r 방향 성분과 theta 방향 성분 계산
    Fr = Fx .* cos(theta) + Fy .* sin(theta); % r 방향 성분
    Ftheta = -Fx .* sin(theta) + Fy .* cos(theta); % theta 방향 성분
 
end