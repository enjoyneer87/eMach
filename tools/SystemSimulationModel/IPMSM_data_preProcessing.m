%% dq plane
%1st coloumn
n=1
subplot(5,3,3*n-2)

% figure
stem3(I_table.Id,I_table.Iq,I_table.Lamda_ds,"LineStyle","none","DisplayName","\lambda_d")
% stem3(i_d,i_q,Lamda_ds,"LineStyle","none");
title("Psi_d");
box on
grid on
xlabel("id");
ylabel("iq")
legend

n=2
subplot(5,3,3*n-2)

% figure
stem3(I_table.Id,I_table.Iq,I_table.Lamda_qs,"LineStyle","none")
title("Psi_q");
xlabel("id");
ylabel("iq");
legend

n=3
subplot(5,3,3*n-2)
% figure
stem3(I_table.Id,I_table.Iq,I_table.torque3_map,"LineStyle","none",'DisplayName','Torque_{meas}- Map')
title("Torque-[Nm]");
xlabel("id");
ylabel("iq");

warning('off','all')
legend
hold on
stem3(I_table.Id,I_table.Iq,torque2_calc,"LineStyle","none",'DisplayName','Torque_{vdvq}-Map')

n=4
subplot(5,3,3*n-2)
stem3(I_table.Id,I_table.Iq,torque2_calc-torque3_map,"LineStyle","none",'DisplayName','Error_{meas-vdvq} -Map')
title("Torque error-[Nm]");
legend
xlabel("id");
ylabel("iq");
% 
% idx=find(iq==750)
% %% voltage 측정이 기본파 기준때문인지 이상함
% I_table.torque3_map(idx)    %
% I_table.torque2_calc(idx)   %
% I_table.Input_torque1_from(idx)   %

n=5
subplot(5,3,3*n-2)
plot(I_table.Input_torque1_from,'DisplayName','Input Torque')
hold on
plot(I_table.torque3_map,'DisplayName','Torque_{meas}- Map')
hold on
plot(I_table.torque2_calc,'DisplayName','Torque_{vdvq}-Map')
Trq_error=reshape((torque2_calc-torque3_map),19,16);
surf(Trq_error,"LineStyle","none",'DisplayName','Error_{meas-vdvq} -Map')
[id,iq]=meshgrid(I_table.Id,I_table.Iq);
hold on
stem3(I_table.Id,I_table.Iq,torque2_calc-torque3_map,"LineStyle","none",'DisplayName','Error_{meas-vdvq} -Map')
hold on
stem3(I_table.Id,I_table.Iq,Input_torque1_from,"LineStyle","none")


%% PMSM Spec
pp =4;
Rs = 0.01;
n_min =1000;
m_max =10000;
Is_max =400*sqrt(2); %Ismax= 400A rms
Vdc =350;
Vsmax=Vdc*(2/pi)*0.98;  % Maximum Modulation Voltage


%% convert unfitted raw data vectors into matrix through gridfit and visually check plots
warning('off', 'all');
% T_calc = -1.5*pp* (Id.*Psiq- Iq.* Psid);


id_axis=linspace(-Is_max,0,50);
iq_axis=linspace(0,Is_max,50);
lamda_d=gridfit(I_table.Id,I_table.Iq,I_table.Lamda_ds,id_axis,iq_axis);
lamda_q=gridfit(I_table.Id,I_table.Iq,I_table.Lamda_qs,id_axis,iq_axis);

%figure
figure
surf(id_axis,iq_axis,lamda_d);
title('Flux_d');
xlabel("id");
ylabel("iq");
%figure
figure
surf(id_axis,iq_axis,lamda_q);
title('Flux_q');
xlabel("id");
ylabel("iq");

Trq_calc=gridfit(I_table.Id,I_table.Iq,torque2_calc,id_axis,iq_axis);
Trq_msr=gridfit(I_table.Id,I_table.Iq,I_table.Input_torque1_from,id_axis,iq_axis);
figure
surf(id_axis,iq_axis,Trq_calc);
hold on
surf(id_axis,iq_axis,Trq_msr);
title('Trq Comparison');
xlabel("id");
ylabel("iq");
figure
surf(id_axis,iq_axis,Trq_msr-Trq_calc);
title('Trq Error')
xlabel("id");
ylabel("iq");

% step 1 calculate the torque contour
figure;
T_step=[1 3 6 10 linspace(15,max(max(abs(Trq_msr))),100)];
T_contour=contour3(id_axis,iq_axis,Trq_msr,T_step);
% T_contour=contour3(id_axis,iq_axis,Trq_calc,T_step);

title('Torque Contour');
xlabel("id");
ylabel("iq");
hold on 
stem3(I_table.Id,I_table.Iq,I_table.Input_torque1_from,"LineStyle","none")
title("TorqueCalc[Nm]");
xlabel("id");
ylabel("iq");

% step 2, define the speed steps
n=(n_min:250:n_max)';

% Step 3, re-arrange data to torque-speed operating points
% T_contour 생성
T_start = 1; % 시작 지점 초기화
data=[];

% 데이터 처리 루프 시작
while T_start < length(T_contour)
    T_stop = T_start + T_contour(2, T_start); % 데이터 덩어리의 끝 인덱스 계산

    % [Trq, Id, Iq] 데이터 생성
    % REPELEM Replicate elements of an array.
    data_temp = [repelem(T_contour(1, T_start), T_contour(2, T_start))' ... % Trq
                 T_contour(1, T_start + 1:T_stop)' ...                      % Id
                 T_contour(2, T_start + 1:T_stop)'];                        % Iq

    % ***** 등고선 데이터 다운샘플링 코드 추가 ****** %
    % 5배로 다운샘플링

    data_downsample = downsample(data_temp, 5);
    
    % 다운샘플된 데이터와 원래 데이터 비교
    % 만약 마지막 행의 Id 또는 Iq 값이 다르면,
    % 마지막 행을 추가하여 데이터 일관성 유지

    if (data_downsample(end, 2) ~= data_temp(end, 2))
        data_temp = [data_downsample; data_temp(end, :)];
    else
    % 그렇지 않으면 다운샘플된 데이터를 그대로 사용
        data_temp = data_downsample;
    end
    % 데이터 합치기    
    % data_temp에 저장된 작은 데이터 덩어리를 data에 합칩니다.
    % 1. 먼저, data_temp를 length(n)번 반복하여 늘립니다. 
    % 이렇게 하면 data_temp의 데이터가 n의 길이만큼 복제됩니다.
    % 2. 그리고 n의 값도 data_temp의 길이만큼 반복하여 생성합니다.
    % 이렇게 하면 n의 값이 data_temp와 동일한 길이로 확장됩니다.
    % 3. 이제, data_replicated와 n_extended를 열 방향으로 합칩니다.
    % 이렇게 하면 data_temp의 복사본이 n 값과 함께 하나의 큰 데이터 행렬 data에 포함됩니다.
    data_replicated = repmat(data_temp, [length(n), 1]);
    n_extended = repelem(n, length(data_temp(:, 1)));
    data = [data; data_replicated, n_extended]; %[Trq, Id, Iq, n]
    % data = [data; repmat(data_temp, [length(n), 1]), repelem(n, T_contour(2, T_start), 1)];
    T_start = T_stop + 1; % 다음 데이터 덩어리의 시작 인덱스 설정    
end

Is=sqrt(data(:,2).^2+data(:,3).^2); % calculated maximum current
flux_d=interp2(id_axis,iq_axis,lamda_d,data(:,2),data(:,3));
flux_q=interp2(id_axis,iq_axis,lamda_q,data(:,2),data(:,3));
flux=sqrt(flux_d.^2+flux_q.^2);
we=2*pi.*data(:,4).*Input.p/2./60;
% calculated modulated voltage
vd=Input.Rs.*data(:,2)-we.*flux_q;
vq=Input.Rs.*data(:,3)+we.*flux_d;
Vs=sqrt(vd.^2+vq.^2); %modulation voltage
IPMSM_MBCData=[data Vs Is]; %[Trq id iq n Vs Is]

% Generate csv data file
header ={'Trq' 'Id' 'Iq' 'n' 'Vs' 'Is'};
xlswrite('.\IPMSM_MBCData.xlsx',header,'sheet1');
xlswrite('.\IPMSM_MBCData.xlsx',IPMSM_MBCData,'sheet1','A2');
clearvars -except IPMSM_MBCData Is_max Vs_max