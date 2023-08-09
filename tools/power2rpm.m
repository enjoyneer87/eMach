function rpm=power2rpm(kw,torque)    
    % 모터의 kW와 토크(Nm)로부터 해당 rpm을 계산하는 함수
    % kW = 토크(Nm)*rad/sec    
    radsec = kw*1000 / (torque);
    rpm=radsec2rpm(radsec);      % 1분에 2 * pi 라디안이 회전하는 것을 고려해 2 * pi / 60으로 나눠줍니다.
end
