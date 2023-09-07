% 함수 1: 전류 테이블 생성
function [I_table, Input] = tempCreateCurrentTable()
    % 기본 입력 설정
    Input.n_max = 5000;
    Input.Rs = 0.0067;
    Input.p = 12;
    Input.Vdc = 650;  % 추가된 변수
    Input.Vs_max = Input.Vdc * (2/pi) * 0.98;  % 추가된 변수
    Input.Is_max = 750;  % 추가된 변수
    Input.test_rpm = 1100;
    Input.plot_rpm = 1100;
    Input.Wr_test = 2 * pi * Input.test_rpm / 60 * Input.p / 2;  % 추가된 변수
    Input.Wr_plot = 2 * pi * Input.plot_rpm / 60 * Input.p / 2;  % 추가된 변수
    Input.n_min = 50;
    
    Ipk = 0:50:Input.Is_max;  % 수정된 변수
    beta = 0:5:90;
    I_pk = repmat(Ipk', length(beta), 1);
    phase_advance = repmat(beta', length(Ipk), 1);
    i_d = I_pk .* cos(deg2rad(phase_advance + 90));
    i_q = I_pk .* sin(deg2rad(phase_advance + 90));
    I_table = table(I_pk, phase_advance, i_d, i_q);
    I_table.Properties.VariableNames = {'Iph', 'phase_advance', 'Id', 'Iq'};
    I_table = sortrows(I_table,'phase_advance','ascend');
    I_table = sortrows(I_table,'Iph','ascend');
end
