% 함수 1: 전류 테이블 생성
function [I_table, Input] = createCurrentTable(Input)
    % 기본 입력 설정
    
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
