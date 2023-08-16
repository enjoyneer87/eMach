function motorSplitStruct=calcVehicleLateralDynamics(vehicleVariable,vehiclePerformData,motorRatios)

    %%%%%%%%%%%%%%%%%%%%%%%% 입력 파라미터 %%%%%%%%%%%%%%%%%%%%
    
    cvw = vehicleVariable.Mass_MotorLAB;                                       % 공차중량 [kg]
    load = 0;                                       % 부하무게 [kg]
    person = 0;                                      % 1인당 몸무게 [kg]
    no_person = 1;                                    % 탑승인원 [명]
    gvw = cvw+load+(person*no_person);                % 차량 총중량 [kg]
    
    da =   1.225                       ;                              % 공기밀도 [kg/m2]              % 1.253;                      
    fa =   vehicleVariable.A_f_MotorLAB;                                                       % Frontal Area [m2]            % 3.42;                        
    ca =   vehicleVariable.C_d_MotorLAB;                                                       % Air Drag Coefficient         % 0.5;                             
    tr =   vehicleVariable.R_w_MotorLAB;                                                         % Tire Radius [m]              % 0.274;                       
    cr =   vehicleVariable.K_r_MotorLAB;                                                         % Rolling Coefficient          % 0.01;                            
    gr =   vehicleVariable.N_d_MotorLAB;                                                     % Gear Ratio (차동기어 포함)    % 8.35;                                    
    ge =   vehicleVariable.gearEfficiency;                                                     % Gear Efficiency              % 0.98;                        
    ga =   9.81;                                                     % 중력가속도 [m/s2]             % 9.81; 
           
    dif_grade = 10;                                    % 등판 간격 [%]
    max_grade = 100;                                   % 최대 등판 각도 [%]
    rot_iner = vehicleVariable.rot_iner;                                % Rotor Inertia [kg*m2]
    
    
    
    %%%%%%%%%%%%%%%%%%%%%%%%%% Data Read %%%%%%%%%%%%%%%%%%%%%%
    
    % f_name_Load = 'DP.xlsx';                  % 엑셀파일 명은 반드시 DP
    % fid_T_Load = fopen(f_name_Load, 'r');
    %   while fid_T_Load < 0
    %       fid_T_Load = fopen(f_name_Load, 'r');
    %   end
    % fclose(fid_T_Load);
    % 
    % data_read = xlsread(f_name_Load);
    % kph = data_read(:, 1);
    % cont_f = data_read(:, 2);
    % max_f = data_read(:, 3);
    
    kph=vehiclePerformData.speed_kph;
    
    %%%%%%%%%%%%%%%%%%%%% 부하 계산 %%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    rol_load = [];
    cli_load = [];
    aero_load = 0.5*da*ca*fa*(kph*1000/3600).^2;
    total_load = [];
    
    aero_load_length = length(aero_load);
    
    
    for t = 0 : dif_grade : max_grade
        
      grade_tan = atan(t/100)*180/pi;
      rol_resis=cr*gvw*ga*cos(grade_tan*pi/180);
      cli_resis=gvw*ga*sin(grade_tan*pi/180);
      rol_load = [rol_load; t rol_resis];   
      cli_load = [cli_load; t cli_resis];
      
      total_load = [total_load aero_load+rol_resis*ones(aero_load_length,1)+cli_resis*ones(aero_load_length,1)];
        
    end
    
    
    cont_f=0.4*vehiclePerformData.force_newtons;
    max_f=vehiclePerformData.force_newtons;
    
    %%%%%%%%%%%%%%%%%%%%%%%%%% 각 운전 변수 계산 %%%%%%%%%%%%%%%%%
    
    dri_shaft_rpm = kph*1000/(2*pi*60*tr);
    rpm = dri_shaft_rpm*gr;
    
    dri_shaft_cont_t = cont_f*tr;
    dri_shaft_max_t = max_f*tr;
    
    dri_shaft_cont_p = dri_shaft_cont_t.*2*pi.*rpm./(1000*60*gr);
    % dri_shaft_max_p = dri_shaft_max_t*2*pi*rpm.'/(1000*60*gr);
    dri_shaft_max_p = dri_shaft_max_t.*2*pi.*rpm/(1000*60*gr);

    motor_cont_p = dri_shaft_cont_p/ge*1000;
    motor_max_p = dri_shaft_max_p/ge*1000;
    motor_max_kW = motor_max_p/1000;
    motor_cont_t = motor_cont_p./(2*pi*rpm./60);
    motor_max_t = motor_max_p./(2*pi*rpm./60);
    
    
    %%%%%%%%%%%%%%%%%%%%%%% 가속 성능 %%%%%%%%%%%%%%%%%%%%%%%%%%%
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
    
    %% 그래프
    
    figure(1)
    hold on
    % grid on
    ylabel('Force [N]');
    xlabel('Speed [kph]');
    title('Maximum Vehicle Speed');
    plot(kph, total_load(:, 1), 'LineWidth' ,2,'DisplayName','Total Load')
    % plot(kph, cont_f, 'LineWidth',2,'DisplayName','')
    plot(kph, max_f, 'LineWidth',2)
    formatter_sci;

    figure(2)
    hold on
    grid on
    ylabel('Force [N]');
    xlabel('Speed [kph]');
    title('Vehicle Gradeability');
    for m = 1 : 1 : (max_grade/dif_grade)+1
      plot(kph, total_load(:, m), 'LineWidth',2,'Color','k');
      hold on
    end
      % plot(kph, cont_f, 'LineWidth',2,'Color','b');
      plot(kph, max_f, 'LineWidth',2,'Color','r');
    formatter_sci
    
    figure(3)
    hold on
    grid on
    ylabel('Torque [Nm]');
    xlabel('Speed [rpm]');
    % plot(rpm, motor_cont_t, 'LineWidth',2)
    plot(rpm, motor_max_t, 'LineWidth',2,'DisplayName',['Gear Ratio:' ,num2str(gr)]);
    title('Total Required Motor TN');

    legend
    formatter_sci
    
    figure(5)
    hold on
    grid on
    ylabel('Time [sec]');
    xlabel('Speed [kph]');
    title('Acceleration Time');
    plot(kph, apro_time_plot, 'LineWidth', 2)
    formatter_sci

    figure(4)
    hold on
    grid on
    ylabel('Power [kW]');
    xlabel('Speed [rpm]');
    title('Total Required Motor PN');
    % plot(rpm, motor_cont_p, 'LineWidth',2)
    plot(rpm, motor_max_p/1000, 'LineWidth',2,'DisplayName',['Gear Ratio:' ,num2str(gr)]);
    legend
    formatter_sci;

    figure(8)
    hold on
    grid on
    ylabel('Power [hp]');
    xlabel('Speed [mph]');
    title('Total Required Motor PN');
    % plot(rpm, motor_cont_p, 'LineWidth',2)
    plot(kph2mph(vehiclePerformData.speed_kph), kw2hp(motor_max_p/1000), 'LineWidth',2,'DisplayName',['Front Motor -Gear Ratio:' ,num2str(gr)]);
    % plot(vehiclePerformData.speed_kph,motor_max_p/1000/3)
    legend
    % plot(rpm, 2*motor_max_p/1000/3, '--','DisplayName',['Rear 2Motor - Gear Ratio:' ,num2str(gr)])

    formatter_sci;

    motorCurve=table(rpm,motor_max_t,motor_max_kW);
    %%
    motorSplitStruct = divideMotorByRatios(motorCurve, motorRatios);

    figure(6)
    hold on
    grid on
    ylabel('Torque [Nm]');
    xlabel('Speed [rpm]');
    title('Each Required Motor TN');
    % plot(rpm, motor_cont_t, 'LineWidth',2)
    plot(rpm, motor_max_t/3, 'LineWidth',2,'DisplayName',['Front Motor -Gear Ratio:' ,num2str(gr)])
    legend
    % plot(rpm, 2*motor_max_t/3, '--','DisplayName',['Rear 2Motor - Gear Ratio:' ,num2str(gr)])
    formatter_sci
    
    figure(7)
    hold on
    grid on
    ylabel('Power [kW]');
    xlabel('Speed [rpm]');
    title('Each Required Motor PN');
    % plot(rpm, motor_cont_p, 'LineWidth',2)
    plot(rpm, motor_max_p/1000/3, 'LineWidth',2,'DisplayName',['Front Motor -Gear Ratio:' ,num2str(gr)]);
    % plot(vehiclePerformData.speed_kph,motor_max_p/1000/3)
    legend
    % plot(rpm, 2*motor _max_p/1000/3, '--','DisplayName',['Rear 2Motor - Gear Ratio:' ,num2str(gr)])
end
