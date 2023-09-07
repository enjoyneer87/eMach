% 함수 3: 자속 맵 생성
function I_table = createFluxMaps(I_table, Input)
    % 자속 맵 생성 코드
    % Wr_test와 Wr_plot을 사용하여 Lamda_ds와 Lamda_qs를 계산합니다.
    
    % Lamda_ds 계산
    Vqs_t = I_table.Vqs_t; % 전압 데이터
    Rs = Input.Rs; % 내부 저항
    Iq = I_table.Iq; % Q 축 전류
    Lamda_ds = (Vqs_t - Rs .* Iq) ./ Input.Wr_test;
    
    % Lamda_qs 계산
    Vds_t = I_table.Vds_t; % 전압 데이터
    Id = I_table.Id; % D 축 전류
    Lamda_qs = -(Vds_t - Rs .* Id) ./ Input.Wr_test;
    
    % 결과를 I_table에 추가
    I_table.Lamda_ds = Lamda_ds;
    I_table.Lamda_qs = Lamda_qs;
end




