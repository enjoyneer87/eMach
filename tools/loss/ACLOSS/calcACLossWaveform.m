function P_rect_waveform = calcACLossWaveform(lactive, w, h, rho, B_time, t)
    % lactive: 도체의 활성 길이 [m]
    % w: 도체의 폭 [m]
    % h: 도체의 높이 [m]
    % rho: 도체의 비저항 [Ohm*m]
    % B_time: 시간에 따른 자속 밀도 [T]
    % t: 시간 벡터 [s]

    % 시간에 따른 자속 밀도의 변화량 (dB/dt)
    dB_dt = diff(B_time) ./ diff(t);

    % 손실 파형 계산
    P_rect_waveform = (lactive * w * h^3 / (12 * rho)) .* (dB_dt).^2;

    % 손실 파형과 시간 벡터의 길이를 맞추기 위해 NaN 값을 추가
    P_rect_waveform = [P_rect_waveform; P_rect_waveform(1)];  % 첫 번째 요소는 NaN
end
