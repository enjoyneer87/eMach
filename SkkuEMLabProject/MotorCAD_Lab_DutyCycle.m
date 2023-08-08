function output = MotorCAD_Lab_DutyCycle(mcad, mcad_file_dir, mcad_file_name, input)

% 임시 
% mcad=actxserver('motorcad.appautomation');
% mcad_file_dir='E:\2023_Task\etc\14_EMLAB_TractionMotor\04_CODE\MCADSpary';
% mcad_file_name='Model1e2Spray2023';

%% 셋팅
% mcad.set_variable("MessageDisplayState", 2)

% Duty Cycle - Calculation
input.DutyCycleType_Lab                          = 1;        % Duty Cycle - Duty Cycle Type : Automotive Drive Cycle
input.DrivCycle_MotorLAB                         = 18;       % Duty Cycle - Automotive Drive Cycle : WLTP Class 3
input.LabThermalCoupling_DutyCycle               = 0;        % Duty Cycle - Thermal Transient Coupling : No coupling (default)
input.Mass_MotorLAB                              = [];       % Vehicle Model - Mass
input.K_r_MotorLAB                               = [];       % Vehicle Model - Rolling Resistance
input.rho_MotorLAB                               = [];       % Vehicle Model - Air Density
input.B_cont_MotorLAB                            = [];       % Vehicle Model - Generating Torque Ratio
input.A_f_MotorLAB                               = [];       % Vehicle Model - Frontal Area
input.C_d_MotorLAB                               = [];       % Vehicle Model - Drag Coefficient
input.N_d_MotorLAB                               = [];       % Vehicle Model - Gear Ratio
input.TorqueCapTrue_MotorLAB                     = false;    % Vehicle Model - Max. Torque : "Off"
input.TorqueCap_MotorLAB                         = [];       % Vehicle Model - Max. Torque
input.R_w_MotorLAB                               = [];       % Vehicle Model - Wheel Radius
input.WheelInertia                               = [];       % Vehicle Model - Wheel Inertia
input.M_o_MotorLAB                               = [];       % Vehicle Model - Mass Correction Factor
input.T_cont_MotorLAB                            = [];       % Vehicle Model - Motoring Torque Ratio
input.SpeedCapTrue_MotorLAB                      = false;    % Vehicle Model - Max. Speed
input.SpeedCap_MotorLAB                          = [];       % Vehicle Model - Max. Speed

% duty cycle 해석 실행 & 결과 자동 저장 'MotorLAB_drivecycledata'
setMcadVariable(input,mcad);
mcad.CalculateDutyCycle_Lab();

% 파일 복사
temp_data_file_path=fullfile(mcad_file_dir, mcad_file_name, 'Lab', 'MotorLAB_drivecycledata');
temp_time=clock;
data_file_path=[temp_data_file_path, '_', num2str(temp_time(4)), 'h', num2str(temp_time(5)), 'm'];
movefile([temp_data_file_path, '.mat'], [data_file_path, '.mat'])

% data 불러오기
data=load([data_file_path, '.mat']);

%% 계산
    % 전자계 토크 무의미
    % 효율 = 샤프트 토크 / (샤프트 토크 + 토탈 로스)
    % 터미널 파워 = 샤프트 토크 / 효율 = 샤프트 토크 + 토탈 로스
    % 드라이빙 사이클 파워 = ? / 역률 아님, 가속 아님
    % 파워 팩터 미사용 ?
SumOfTerminalPower=sum(data.Terminal_Power);
PositiveSumOfTerminalPower=0;
for j=1:length(data.Terminal_Power(:,1))
    if data.Terminal_Power(j,1)>0
        PositiveSumOfTerminalPower=PositiveSumOfTerminalPower+data.Terminal_Power(j,1);
    end
end

SumOfDriveCyclePower=sum(data.Drive_Cycle_Power);
PositiveSumOfDriveCyclePower=0;
for j=1:length(data.Drive_Cycle_Power(:,1))
    if data.Drive_Cycle_Power(j,1)>0
        PositiveSumOfDriveCyclePower=PositiveSumOfDriveCyclePower+data.Drive_Cycle_Power(j,1);
    end
end

SumOfTotalLoss=sum(data.Total_Loss);

TerminalPowerIncludingPowerFactor=data.Terminal_Power./data.Power_Factor;
SumOfTerminalPowerIncludingPowerFactor=0;
for j=1:length(TerminalPowerIncludingPowerFactor)
    if TerminalPowerIncludingPowerFactor(j,1)~=Inf
        SumOfTerminalPowerIncludingPowerFactor=SumOfTerminalPowerIncludingPowerFactor+TerminalPowerIncludingPowerFactor(j,1);
    end
end
PositiveSumOfTerminalPowerIncludingPowerFactor=0;
for j=1:length(TerminalPowerIncludingPowerFactor)
    if TerminalPowerIncludingPowerFactor(j,1)~=Inf && TerminalPowerIncludingPowerFactor(j,1)>0
        PositiveSumOfTerminalPowerIncludingPowerFactor=PositiveSumOfTerminalPowerIncludingPowerFactor+TerminalPowerIncludingPowerFactor(j,1);
    end
end


output=;
end