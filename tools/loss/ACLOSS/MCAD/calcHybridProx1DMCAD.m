function P_rect = calcHybridProx1DMCAD(w, h, sigma, freqE,lactive, Bm)
    % calculatePowerLossRect - 사각형 도체의 전력 손실을 계산합니다.
    % w = gamma_w
    % h = gamma_h
    % delta = 1 ./ sqrt(pi * mu_c * sigma .* double(freqE)); %[m]
    % 사각형 도체에 대한 무차원 매개변수
    % gamma_w = w ./ delta;
    % gamma_h = h ./ delta;  
    % 주어진 수식을 바탕으로 전력 손실 계산
    % omega
    omegaE=freq2omega(freqE);
    tempValue=2;
    P_rect = (1/tempValue)*1/12*(lactive*(w*h^3)*sigma)*(omegaE.^2.*Bm.^2);   %[W]

    % 기존 변수들: lactive, w, h, sigma, omegaE, Bm, delta

    % 사각형 도체의 경우 r은 도체 높이의 절반입니다.
    r = h / 2;  % r = height/2

    % 스킨 깊이를 반영한 면적 비율 계산
    % Ae_A = delta / (2 * r);  % Ae/A 비율

    % 기존 손실 계산에 반영
    % P_rect = 1 / 12 * (lactive * (w * h^3) * sigma * (omegaE.^2 .* Bm.^2) * Ae_A);
     % (mm2m(lactive)*mm2m(Cuboid_Width)*(mm2m(Cuboid_Height))^3. ...
     %     *sigma*(omegaE *B     )^2/divCoeffi) ;

end
