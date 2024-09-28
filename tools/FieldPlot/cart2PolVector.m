function [Fr, Ftheta] = cart2PolVector(Fx, Fy, x, y)
    % Cartesian (x, y) 성분을 Polar (r, theta) 성분으로 변환 (복소수 지원)
    % Fx, Fy: x, y 방향의 물리량 성분 (복소수 가능)
    % x, y: 위치 좌표
    
    sizeFx = size(Fx);
    sizeFy = size(Fy);
    sizex = size(x);
    sizey = size(y);

    % x와 y 좌표의 크기가 맞는지 확인
    if ~isequal(sizex, sizey)
        error('x, y 좌표 크기가 일치하지 않습니다.');
    end

    % x, y 좌표가 열 벡터인지 확인하고, 아니라면 변환
    if sizex(2) < sizex(1)
        x = x';
        y = y';
        sizex = size(x);
    end

    % Fx, Fy가 x, y와 일치하는지 확인하고 변환
    if sizeFx(2) < sizeFx(1)
        Fx = Fx';
        Fy = Fy';
    end

    % 반지름 및 각도 계산
    r = sqrt(x.^2 + y.^2);
    theta = atan2(y, x);
    % 
    %     % r 방향 성분과 theta 방향 성분 계산
    % Fr = Fx .* cos(theta) + Fy .* sin(theta); % r 방향 성분
    % Ftheta = -Fx .* sin(theta) + Fy .* cos(theta); % theta 방향 성분
    
    % 실수 및 허수 부분에 대해 별도로 r, theta 방향 성분 계산
    Fr_real = real(Fx) .* cos(theta) + real(Fy) .* sin(theta);
    Ftheta_real = -real(Fx) .* sin(theta) + real(Fy) .* cos(theta);

    Fr_imag = imag(Fx) .* cos(theta) + imag(Fy) .* sin(theta);
    Ftheta_imag = -imag(Fx) .* sin(theta) + imag(Fy) .* cos(theta);

    % 최종 결과로 복소수 벡터 성분 반환
    Fr = Fr_real + 1i * Fr_imag;
    Ftheta = Ftheta_real + 1i * Ftheta_imag;
end