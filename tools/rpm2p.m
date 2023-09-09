function p = rpm2p(rpm, freqE)
    % freq2rpm 함수의 역 함수
    % omegaE = freq2omega(freqE);    
    % p = (2 * pi * freq * 60) / (2 * pi * omega)
    p = (2 * freqE * 60) / rpm;

end
