function P_rect = calcHybridStrandProx1D(gamma_w, gamma_h, mu, sigma, l, Bm)
    % calculatePowerLossRect - 사각형 도체의 전력 손실을 계산합니다.
    %
    % Syntax: P_rect = calculatePowerLossRect(gamma_w, gamma_h, mu, sigma, l, Bm)
    %
    % Inputs:
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
    P_rect = (gamma_w* gamma_h^3) / (12 * pi^2 * mu^2 * sigma) *( l * Bm.^2);   %[W]
end
