function P_rect = calcHybridProx1D(gamma_w, gamma_h, mu, sigma, lactive, Bm)
    % calculatePowerLossRect - 사각형 도체의 전력 손실을 계산합니다.
    %
    % Syntax: P_rect = calculatePowerLossRect(gamma_w, gamma_h, mu, sigma, l, Bm)
    %
    % Inputs:
    % delta = 1 ./ sqrt(pi * mu_c * sigma .* double(freqE)); %[m]
    % 사각형 도체에 대한 무차원 매개변수
    % gamma_w = w ./ delta;
    % gamma_h = h ./ delta;  
    %   gamma_w - 사각 도체의 폭에 대한 차원 없는 매개변수   
    %   gamma_h - 사각 도체의 높이에 대한 차원 없는 매개변수 
    %   mu - 도체의 투자율                                 [H/m]
    %   sigma - 도체의 전도도                              [S/m]
    %   l - 도체의 길이                                    [m]
    %   Bm - 최대 자기장의 크기                             [T]
    %
    % Outputs:
    %   P_rect - 사각형 도체의 전력 손실

    % 주어진 수식을 바탕으로 전력 손실 계산
    % [FIX 2026-07-14] 분모 12*pi^2 -> 6 수정 (2*pi^2 ~= 19.7배 과소추정 버그).
    % 표준식: P = gamma_w*gamma_h^3/(6*mu^2*sigma)*l*B^2 = sigma*omega^2*w*h^3*l*B^2/24
    % (delta=sqrt(2/(omega*mu*sigma)), gamma=dim/delta 규약에서 MCAD /24 공식과 항등)
    P_rect = (gamma_w* gamma_h^3) / (6 * mu^2 * sigma) *(lactive * Bm.^2);   %[W]

end
