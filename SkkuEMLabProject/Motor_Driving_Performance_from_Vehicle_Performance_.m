% clear
% clc

%%%%%%%%%%%%%%%%%%%%%%%% �Է� �Ķ���� %%%%%%%%%%%%%%%%%%%%

cvw = 2000;                                % �����߷� [kg]
load = 500;                                % ���Ϲ��� [kg]
person = 75;                               % 1�δ� ������ [kg]
no_person = 1;                             % ž���ο� [��]
gvw = cvw+load+(person*no_person);         % ���� ���߷� [kg]
fa = 3.42;                                 % Frontal Area [m2]
ca = 0.5;                                  % Air Drag Coefficient
cr = 0.01;                                 % Rolling Coefficient
tr = 0.274;                                % Tire Radius [m]
gr = 8.35;                                 % Gear Ratio (������� ����)
ge = 0.98;                                 % Gear Efficiency
da = 1.253;                                % ����е� [kg/m2]
ga = 9.81;                                 % �߷°��ӵ� [m/s2]
dif_grade = 2;                             % ���� ���� [%]
max_grade = 1;                            % �ִ� ���� ���� [%]
rot_iner = 0.0877;                         % Rotor Inertia [kg*m2]

%%%%%%%%%%%%%%%%%%%%%%%%%% Data Read %%%%%%%%%%%%%%%%%%%%%%

f_name_Load = 'DP.xlsx';                  % �������� ���� �ݵ�� DP
fid_T_Load = fopen(f_name_Load, 'r');
  while fid_T_Load < 0
      fid_T_Load = fopen(f_name_Load, 'r');
  end
fclose(fid_T_Load);

data_read = xlsread(f_name_Load);
kph = data_read(:, 1);
cont_f = data_read(:, 2);
max_f = data_read(:, 3);

kph=speed_kph;
max_f=force_newtons;

%%%%%%%%%%%%%%%%%%%%%%%%%% �� ���� ���� ��� %%%%%%%%%%%%%%%%%

dri_shaft_rpm = kph*1000/(2*pi*60*tr);
rpm = dri_shaft_rpm*gr;

% dri_shaft_cont_t = cont_f*tr;
dri_shaft_max_t = max_f*tr;

% dri_shaft_cont_p = dri_shaft_cont_t*2*pi*rpm.'/(1000*60*gr);
dri_shaft_max_p = dri_shaft_max_t*2*pi*rpm.'/(1000*60*gr);

% motor_cont_p = dri_shaft_cont_p/ge*1000;
motor_max_p = dri_shaft_max_p/ge*1000;

% motor_cont_t = motor_cont_p/(2*pi*rpm.'/60);
motor_max_t = motor_max_p/(2*pi*rpm.'/60);

%%%%%%%%%%%%%%%%%%%%% ���� ��� %%%%%%%%%%%%%%%%%%%%%%%%%%%%%
rol_load = [];
cli_load = [];
aero_load = 0.5*da*ca*fa*(kph*1000/3600).^2;
total_load = [];

aero_load_length = length(aero_load);


for t = 0 : dif_grade : max_grade;
    
  grade_tan = atan(t/100)*180/pi;
  rol_resis=cr*gvw*ga*cos(grade_tan*pi/180);
  cli_resis=gvw*ga*sin(grade_tan*pi/180);
  rol_load = [rol_load; t rol_resis];   
  cli_load = [cli_load; t cli_resis];
  
  total_load = [total_load aero_load+rol_resis*ones(aero_load_length,1)+cli_resis*ones(aero_load_length,1)];
    
end

%%%%%%%%%%%%%%%%%%%%%%% ���� ���� %%%%%%%%%%%%%%%%%%%%%%%%%%%
kph_diff = [];

for h = 1 : 1 : aero_load_length-1
    kph_di = kph(h+1, :) - kph(h, :);
    kph_diff = [kph_diff; kph_di];
end

accel_numer = (dri_shaft_max_t/tr)-total_load(:,1);
accel_numer(1, :) = 0;
accel_denom = gvw+rot_iner*ge*(gr)^2/(tr^2);
accel = accel_numer/accel_denom;
accel(1, :) = [];
accel_time = [];

for k = 1: 1 : aero_load_length-1
    accel_1 = kph_diff(k, :) * 1000 / 3600 / accel(k, :);
    accel_time = [accel_time; accel_1];
end

apro_time(1, 1) = accel_time(1, 1);

for l = 2: 1 : aero_load_length-1
    apro_ti = accel_time(l, 1) + apro_time(l-1, 1);
    apro_time = [apro_time; apro_ti];
end

apro_time_plot(1,1) = 0;
apro_time_plot = [apro_time_plot; apro_time];

% �׷���

figure(1)
hold on
grid on
ylabel('Force [N]');
xlabel('Speed [kph]');
title('Maximum Vehicle Speed');
% plot(kph, total_load(:, 1), 'LineWidth' ,2)
plot(kph, cont_f, 'LineWidth',2)
plot(kph, max_f, 'LineWidth',2)

figure(2)
hold on
grid on
ylabel('Torque [Nm]');
xlabel('Speed [rpm]');
title('Required Motor Performance');
plot(rpm, motor_cont_t, 'LineWidth',2)
plot(rpm, motor_max_t, 'LineWidth',2)

figure(3)
hold on
grid on
ylabel('Force [N]');
xlabel('Speed [kph]');
title('Vehicle Gradeability');
for m = 1 : 1 : (max_grade/dif_grade)+1
  plot(kph, total_load(:, m), 'LineWidth',2)
end
  plot(kph, cont_f, 'LineWidth',2)
  plot(kph, max_f, 'LineWidth',2)

figure(4)
hold on
grid on
ylabel('Time [sec]');
xlabel('Speed [kph]');
title('Acceleration Time');
plot(kph, apro_time_plot, 'LineWidth', 2)

disp('�Ϸ�');