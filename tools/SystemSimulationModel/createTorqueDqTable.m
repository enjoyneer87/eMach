% 함수 4: 토크 맵 생성
function I_table = createTorqueDqTable(I_table, Input)
    % 토크 맵 생성 코드
    % Wr_plot을 사용하여 토크 맵을 계산합니다.
    
    % 토크 맵 계산
    Id = I_table.Id; % D 축 전류
    Iq = I_table.Iq; % Q 축 전류
    Lamda_ds = I_table.Lamda_ds;
    Lamda_qs = I_table.Lamda_qs;
    p = Input.p;
    TorqueDq = -p/2 * (Id .* Lamda_qs - Iq .* Lamda_ds);
    
    % 결과를 I_table에 추가
    I_table.TorqueDq = TorqueDq;
end

