function acLoss = calcHybridProxImproved1D(gamma_w, gamma_h, mu, sigma, l, Bm)
    % calcAcLoss - AC 손실을 계산합니다.
    %
    % Syntax: acLoss = calcAcLoss(gamma_w, gamma_h, sigma, mu)
    %
    % Inputs:
    %   gamma_w - 사각 도체의 폭에 대한 차원 없는 매개변수
    %   gamma_h - 사각 도체의 높이에 대한 차원 없는 매개변수
    %   sigma - 도체의 전도도 [S/m]
    %   mu - 도체의 투자율 [H/m]
    %
    % Outputs:
    %   acLoss - 계산된 AC 손실 값

    % delta = 1 ./ sqrt(pi * mu_c * sigma .* double(freqE)); %[m]
    %
    % 사각형 도체에 대한 무차원 매개변수
    % gamma_w = w ./ delta;
    % gamma_h = h ./ delta;  
    % g 함수 계산
    gValue = (gamma_w / (sigma * mu^2)) * ...
             (sinh(gamma_h) - sin(gamma_h)) / ...
             (cosh(gamma_h) + cos(gamma_h));
    
    % AC 손실 반환
    acLoss = gValue*( l * Bm.^2);
end