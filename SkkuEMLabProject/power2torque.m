function torque=power2torque(kw,rpm)    
    % 모터의 kW와 토크(Nm)로부터 해당 rpm을 계산하는 함수
    % kW = 토크(Nm)*rad/sec    
    radsec = rpm2radsec(rpm);
    torque = kw*1000 / (radsec);
end
