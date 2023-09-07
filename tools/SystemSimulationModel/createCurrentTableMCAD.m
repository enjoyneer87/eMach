% 함수 1: 전류 테이블 생성
function [I_table, id_index,iq_index,lambda_d,lambda_q] = createCurrentTableMCAD(MotorCADFEA)
    % 기본 입력 설정
    %% Step 1: Load and Preprocess Data

    FEAdata.current.d         =  MotorCADFEA.Id_Peak(:,1)'  ;    
    FEAdata.current.q         =  MotorCADFEA.Iq_Peak(1,:)   ;    
    id = FEAdata.current.d;
    iq = FEAdata.current.q;

    FEAdata.flux.d            =  MotorCADFEA.Flux_Linkage_D';
    FEAdata.flux.q            =  MotorCADFEA.Flux_Linkage_Q';
    lambda_d = FEAdata.flux.d;
    lambda_q = FEAdata.flux.q;


    %Visualize the flux surface
    figure;
    mesh(id,iq,lambda_d);
    xlabel('I_d [A]')
    ylabel('I_q [A]')
    title('\lambda_d'); grid on;
    
    hold on
    surf( MotorCADFEA.Id_Peak, MotorCADFEA.Iq_Peak,MotorCADFEA.Flux_Linkage_D)
    scatter3( MotorCADFEA.Id_Peak, MotorCADFEA.Iq_Peak,MotorCADFEA.Flux_Linkage_D,'k')

    figure;
    mesh(id,iq,lambda_q);
    xlabel('I_d [A]')
    ylabel('I_q [A]')
    title('\lambda_q'); grid on;

    %% Step 2: Generate Evenly Spaced Data
    % Use spline interpolation to get higher resolution
    id_new = linspace(min(id),max(id),flux_d_size);
    iq_new = linspace(min(iq),max(iq),flux_q_size);
    lambda_d_new = interp2(id',iq,lambda_d,id_new',iq_new,'spline');
    lambda_q_new = interp2(id',iq,lambda_q,id_new',iq_new,'spline');
    
    %Visualize the flux surface
    figure;
    mesh(id_new,iq_new,lambda_d_new);
    xlabel('I_d [A]')
    ylabel('I_q [A]')
    title('\lambda_d_{Interp}'); grid on;
    
    figure;
    mesh(id_new,iq_new,lambda_q_new);
    xlabel('I_d [A]')
    ylabel('I_q [A]')
    title('\lambda_q_{Interp}'); grid on;
    %% Step 3: Set Block Parameters
    % Set the breakpoints
    id_index=id_new;
    iq_index=iq_new;
    
    % Set the table data
    lambda_d=lambda_d_new;
    lambda_q=lambda_q_new;
    %% 왜 table을 저렇게 
    I_pk=MotorCADFEA.Stator_Current_Line_Peak;
    phase_advance=MotorCADFEA.Phase_Advance;
    Ipk=I_pk
    beta=phase_advance
    % Ipk = 0:50:Input.Is_max;  % 수정된 변수
    % beta = 0:5:90;
    % B = repmat(A, m, n)
    % A는 반복하고자 하는 원본 배열입니다.
    % m은 원본 배열 A를 행 방향으로 반복하는 횟수입니다.
    % n은 원본 배열 A를 열 방향으로 반복하는 횟수입니다.
    I_pk = repmat(Ipk', length(beta),1);
    phase_advance = repmat(beta', length(Ipk), 1);
    % i_d = I_pk .* cos(deg2rad(phase_advance + 90));
    % i_q = I_pk .* sin(deg2rad(phase_advance + 90));
    
    
    i_d=MotorCADFEA.Id_Peak;
    i_q=MotorCADFEA.Iq_Peak;
    % [I_pk,phase_advance]=dq2pkBeta(i_d,i_q);
    %%
    
    flatten_Id_Peak = MotorCADFEA.Id_Peak(:);
    flatten_Iq_Peak = MotorCADFEA.Iq_Peak(:);
    flatten_lamda_d = MotorCADFEA.Flux_Linkage_D(:);
    flatten_lamda_q = MotorCADFEA.Flux_Linkage_Q(:);

    I_table = table(I_pk, phase_advance, i_d, i_q);
    I_table.Properties.VariableNames = {'Iph', 'phase_advance', 'Id', 'Iq'};
    I_table = sortrows(I_table,'phase_advance','ascend');
    I_table = sortrows(I_table,'Iph','ascend');
end
