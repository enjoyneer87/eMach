% 함수 2: 전압 테이블 생성
function I_table = createVoltageTable(I_table)
    % 전압 테이블 생성 코드
    % 여기서는 파일에서 읽어온 데이터를 I_table에 추가하는 부분만 포함하였습니다.
    fileDir = 'Z:\01_Codes_Projects\git_Motor_System_Model\SKKU_RT\SKKU_LUT\';
    Vds_t = readmatrix(fullfile(fileDir, 'vd_ipk_beta.csv'));
    Vqs_t = readmatrix(fullfile(fileDir, 'vq_ipk_beta.csv'));
    Vds_t = reshape(Vds_t, [], 1);
    Vqs_t = reshape(Vqs_t, [], 1);
    Vabs_s = sqrt(Vds_t.^2 + Vqs_t.^2);
    I_table = addvars(I_table, Vds_t, Vqs_t, Vabs_s, 'after', 'Iq');
end