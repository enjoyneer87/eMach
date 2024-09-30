function [Fr, Ftheta] = cart2PolVector(Fx, Fy, x, y)
    % Cartesian (x, y) 성분을 Polar (r, theta) 성분으로 변환 (복소수 지원)
    % Fx, Fy: x, y 방향의 물리량 성분 (복소수 가능)
    % x, y: 위치 좌표
    
    sizeFx = size(Fx);
    sizeFy = size(Fy);
    sizex = size(x);
    sizey = size(y);
    
    Fx=Fx';
    Fy=Fy';
    % 반지름 및 각도 계산
    % r = sqrt(x.^2 + y.^2);
    theta = atan2(y, x);
    % 
    %     % r 방향 성분과 theta 방향 성분 계산
    % Fr = Fx .* cos(theta) + Fy .* sin(theta); % r 방향 성분
    % Ftheta = -Fx .* sin(theta) + Fy .* cos(theta); % theta 방향 성분
    
    % 실수 및 허수 부분에 대해 별도로 r, theta 방향 성분 계산
    Fr_real = real(Fx) .* repmat(cos(theta),1,size(Fx,2)) + real(Fy) .* repmat(sin(theta),1,size(Fy,2)) ;
    Ftheta_real = -real(Fx) .* repmat(sin(theta),1,size(Fy,2))+ real(Fy) .* repmat(cos(theta),1,size(Fx,2));

    Fr_imag = imag(Fx) .* repmat(cos(theta),1,size(Fx,2)) + imag(Fy) .* repmat(sin(theta),1,size(Fy,2));
    Ftheta_imag = -imag(Fx) .* repmat(sin(theta),1,size(Fy,2)) + imag(Fy) .*  repmat(cos(theta),1,size(Fx,2)); ;

    % 최종 결과로 복소수 벡터 성분 반환
    Fr = Fr_real + 1i * Fr_imag;
    Ftheta = Ftheta_real + 1i * Ftheta_imag;
end