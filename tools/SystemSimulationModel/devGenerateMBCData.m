function IPMSM_MBCData = devGenerateMBCData(I_table, T_contour, n_min, n_max, id_axis, iq_axis, lamda_d, lamda_q, torque2_calc, n)
    % 이 함수는 MBC 데이터를 생성합니다.
    
    % I_table로부터 필요한 데이터 추출
    Id = I_table.Id;
    Iq = I_table.Iq;
    Lamda_ds = I_table.Lamda_ds;
    Lamda_qs = I_table.Lamda_qs;
    Input_torque1_from = I_table.Input_torque1_from;
    Vds_t = I_table.Vds_t;
    Vqs_t = I_table.Vqs_t;
    Vabs_s = I_table.Vabs_s;
    torque3_map = I_table.torque3_map;
    
    % 여기에 추가 데이터 처리 및 계산 코드를 추가합니다.
    
    % 최종 결과인 IPMSM_MBCData를 반환합니다.
end
