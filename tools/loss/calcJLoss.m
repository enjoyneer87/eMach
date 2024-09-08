function P = calcJLoss(Jrms, V, rho)
    % calculateLoss - 전류 밀도와 도체 부피를 사용하여 손실량을 계산하는 함수
    %
    % 사용법:
    %   P = calculateLoss(J, V, rho)
    %
    % 입력 매개변수:
    %   J   - 전류 밀도 (A/m²)
    %   V   - 도체 부피 (m³)
    %   rho - 도체의 전기 저항률 (Ω·m)
    %
    % 출력 매개변수:
    %   P   - 손실량 (W, 와트)

    % 손실량 계산
    P = Jrms.^2 * rho * V;
end