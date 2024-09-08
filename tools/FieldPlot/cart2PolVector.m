function [Fr, Ftheta] = cart2PolVector(Fx, Fy, x, y)
    % Cartesian (x, y) 성분을 Polar (r, theta) 성분으로 변환
    % Fx, Fy: x, y 방향의 물리량 성분
    % x, y: 위치 좌표

    % 반지름과 각도 계산
    r = sqrt(x.^2 + y.^2);
    theta = atan2(y, x);

    % r 방향 성분과 theta 방향 성분 계산
    Fr = Fx .* cos(theta) + Fy .* sin(theta); % r 방향 성분
    Ftheta = -Fx .* sin(theta) + Fy .* cos(theta); % theta 방향 성분
end