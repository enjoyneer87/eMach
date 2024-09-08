function [P_rect,P_1DInstant,P_1DrectG1,P1DrectG2, P_rect_nonGamma, P_rectMCAD1D, P_2DG1,P_2DG2] = calcHybridACLossWave(conductorType, dimensions, freqE, BField)
    % 물리 상수 및 도체 속성 설정
    elec.T0.resistivity = 1.724E-8;   % 저항값 (옴·미터)
    sigma = 1 / elec.T0.resistivity;  % 전기전도도 (S/m)
    rho   = 1/sigma; 
    mu0 = 4*pi*10^-7;                 % [H/m]
    mu_c = mu0;                       % 도체와 공기 중 투자율이 같은 것으로 가정
    omegaE = freq2omega(freqE);       % 각주파수 계산

    % 스킨 깊이 계산
    % delta = 1 ./ sqrt(pi * mu_c * sigma .* double(freqE)); % 스킨 깊이 [m]
    delta = 1 ./ sqrt(pi * mu_c * sigma .* double(freqE)); % 스킨 깊이 [m]

    lactive = mm2m(dimensions(3)); % 활성 길이 [m]

    % 도체 형태에 따른 계산 수행
    switch conductorType
        case 'rectangular'
            % 도체의 폭과 높이를 [mm]에서 [m]로 변환
            w = mm2m(dimensions(1)); % 폭 [m]
            h = mm2m(dimensions(2)); % 높이 [m]

            % 사각형 도체에 대한 수정된 스킨 깊이 계산
            % if delta  > w
            delta_w_prime = delta .* sqrt((w + h) / (2 * h));
            delta_h_prime = delta .* sqrt((w + h) / (2 * w));

            % 무차원 형상 파라미터 계산
            gamma_w = w ./ delta;
            gamma_h = h ./ delta;
            gamma_w_prime = w ./ delta_w_prime;
            gamma_h_prime = h ./ delta_h_prime;
        
            %% Formula A
            % f1 함수 정의
            f1_func = @(gamma) (1 / (8 * pi * sigma * mu_c^2)) * gamma.^4;
            % g1 함수 정의
            g1_func = @(gamma_w, gamma_h) (gamma_w .* gamma_h.^3) / (6 * pi^2 * mu_c^2 * sigma);
            %% Formula B
            % g2 함수 정의
            g2_func = @(gamma_w, gamma_h) (gamma_w / (sigma * mu_c^2)) * ...
                (sinh(gamma_h) - sin(gamma_h)) / (cosh(gamma_h) + cos(gamma_h));    

            % BField가 구조체인지 확인 (Br, Btheta 포함)
            if isfield(BField,'Br')
                Br = BField.Br;
                Btheta = BField.Bthetam;
                Bm = sqrt(Br.^2 + Btheta.^2);
                % AC 손실 계산
                P_1DInstant=[];
                P_rect                 = calcHybridProx1D(gamma_w_prime, gamma_h_prime, mu_c, sigma, lactive, Bm); %[W
                % P_rect              = calcHybridProx1D(gamma_w_prime(1), gamma_h_prime(1), mu0, sigma, lactive, Bm); %[W]
                P_1DrectG1             = lactive * g1_func(gamma_w_prime, gamma_h_prime) .* Bm.^2 ;
                P1DrectG2              = lactive * g2_func(gamma_w_prime, gamma_h_prime) .* Bm.^2 ;
                P_rect_nonGamma        = calcHybridProx1D(w, h, mu0, sigma, lactive, Bm); %[W]
                P_rectMCAD1D           = calcHybridProx1DMCAD(w, h, sigma, freqE, lactive, Bm); %[W]

                % 2D 방법에 의한 손실 계산
                P_2DG1 = lactive * (g1_func(gamma_w_prime, gamma_h_prime) .* Br.^2 + ...
                                  g1_func(gamma_h_prime, gamma_w_prime) .* Btheta.^2);
                % 2D 방법에 의한 손실 계산
                P_2DG2 = lactive * (g2_func(gamma_w_prime, gamma_h_prime) .* Br.^2 + ...
                                  g2_func(gamma_h_prime, gamma_w_prime) .* Btheta.^2);
            else
                % 1D 정보만 입력된 경우
                Bm = BField.dataTable.GraphValue;
                t= BField.dataTable.Time;
                P_1DInstant = calcACLossWaveform(lactive, w, h, rho, Bm, t);            
                P_rect              = calcHybridProx1D(gamma_w_prime(1), gamma_h_prime(1), mu_c, sigma, lactive, Bm); %[W                
                P_1DrectG1 = lactive * g1_func(gamma_w_prime, gamma_h_prime) .* Bm.^2 ;
                P1DrectG2 = lactive  * g2_func(gamma_w, gamma_h) .* Bm.^2 ;
                % P_rect       = calcHybridProx1D(gamma_w_prime(1), gamma_h_prime(1), mu0, sigma, lactive, Bm); %[W]
                P_rectMCAD1D = calcHybridProx1DMCAD(w, h, sigma, freqE, lactive, Bm); %[W]
                % P_rectMCAD1D = calcHybridProx1DMCAD(gamma_w, gamma_h, sigma, freqE, lactive, Bm); %[W]
                P_rect_nonGamma = []; % 값이 없는 경우 빈 배열 할당
                P_2DG1 =[];
                P_2DG2 = []; % 값이 없는 경우 빈 배열 할당
            end

        case 'circular'
            % 원형 도체의 계산 (현재 구현되지 않음)
            error('Circular conductor type is not currently implemented.');

        otherwise
            error('Unsupported conductor type. Choose either "rectangular" or "circular".');
    end
end