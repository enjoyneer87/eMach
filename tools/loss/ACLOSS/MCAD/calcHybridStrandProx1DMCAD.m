function P_rect = calcHybridStrandProx1DMCAD(w, h, sigma, freqE,l, Bm)
    % calculatePowerLossRect - 사각형 도체의 전력 손실을 계산합니다.

    % 주어진 수식을 바탕으로 전력 손실 계산
    P_rect =  1/12*(l*(w*h^3)*sigma*freqE^2).*Bm.^2;   %[W]
end
