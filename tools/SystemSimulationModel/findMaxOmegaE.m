function omega_e_max = findMaxOmegaE(lambda_d, lambda_q, i_d, i_q, R_s, PhaseVoltageRms)
    % 초기 오메가e 추정치 설정
    omega_e = 0;
    step = 1; % 오메가e 증가량
    
    while true
        % Vd와 Vq 계산
        V_d = R_s * i_d - omega_e * lambda_q;
        V_q = R_s * i_q + omega_e * lambda_d;
        
        % Vrms 계산
        V_rms = sqrt((V_d^2 + V_q^2) / 2);
        
        % Vrms가 PhaseVoltageRms를 초과하는지 검사
        if V_rms > PhaseVoltageRms
            % V_rms가 초과하면 마지막 유효한 omega_e 반환
            omega_e_max = omega_e - step;
            break;
        end
        
        % omega_e 증가
        omega_e = omega_e + step;
    end
end
