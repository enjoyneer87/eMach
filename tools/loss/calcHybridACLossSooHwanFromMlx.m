function W_AC_a = calcHybridACLossSooHwan(J_e, J_f, S, L, sigma)
    % J_e: 전류와 자기장이 모두 존재할 때의 요소별 전류밀도
    % J_f: 자기장만 존재할 때의 요소별 전류밀도
    % S: 각 요소의 단면적
    % L: 도체의 길이
    % sigma: 도체의 전도도
    % 도체별 요소 전류밀도 제곱 x 요소 면적 sum
    % 전류밀도의 차이 제곱에 대한 손실 계산
    delta_J_squared = (J_e.^2 - J_f.^2);
    
    % 각 요소에 대한 AC 손실 계산 및 총합
    W_AC_a = sum((1/sigma) * delta_J_squared .* S * L);
end