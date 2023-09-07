% 함수 4: 토크 맵 생성
function MotorCADFEA = createTorqueDqMap(MotorCADFEA, Input)
    % 토크 맵 생성 코드
    % Wr_plot을 사용하여 토크 맵을 계산합니다.
    
    Id = MotorCADFEA.Id_Peak; % D 축 전류
    Iq = MotorCADFEA.Iq_Peak; % Q 축 전류
    Lamda_ds = MotorCADFEA.Flux_Linkage_D;
    Lamda_qs = MotorCADFEA.Flux_Linkage_Q;
    p = Input.p;
    % Id = Id/sqrt(2);
    % Iq = Iq/sqrt(2);
    TorqueDq = -p/2 * (Id .* Lamda_qs - Iq .* Lamda_ds);
    TorqueDq = convertInvPowerInvariance(TorqueDq);
    % 결과를 I_table에 추가
    MotorCADFEA.TorqueDq = TorqueDq;
end

