function BasePointOutput = calcMotorCADLabBasePoint(mcad, mcad_file_dir, mcad_file_name, input)

% 임시 
% mcad=actxserver('motorcad.appautomation');
% mcad_file_dir='E:\2023_Task\etc\14_EMLAB_TractionMotor\04_CODE\MCADSpary';
% mcad_file_name='Model1e2Spray2023';
% data=load('E:\2023_Task\etc\14_EMLAB_TractionMotor\04_CODE\MCADSpary\Model1e2Spray2023\Lab\MotorLAB_elecdata_copy.mat');

%% 셋팅
% Calculation - General
input.DCBusVoltage                               = 2400;      % Drive - DC Bus Voltage
input.ModulationIndex_MotorLAB                   = 0.95;     % Drive - Maximum Modulation Index
input.OperatingMode_Lab                          = 0;        % Drive - Operating Mode : Motor
input.ControlStrat_MotorLAB                      = 0;        % Drive - Control Stratey : Maximum Torque/Amp
input.DCCurrentLimit_Lab                         = 0;        % Drive - DC Current Limit : None

input.MagnetLossBuildFactor                      = 1 ;       % Losses - Magnet Loss Build Factor
input.StatorIronLossBuildFactor                  = 1 ;       % Losses - Iron Loss Build Factors - Stator
input.RotorIronLossBuildFactor                   = 1 ;       % Losses - Iron Loss Build Factors - Rotor

% input.TurnsRef_MotorLAB                          = [];       % Scaling
% input.ResistanceTurnsRef_MotorLAB                = [];       % Scaling
input.TurnsCalc_MotorLAB                         = 1;        % Scaling - Turns / Coil - Calculation

% input.Length_Ref_Lab                             = [];       % Scaling
% input.Length_Ref_Resistance_Lab                  = [];       % Scaling
% input.Length_Calc_Lab                            = [];       % Scaling - Active Length - Calculation

input.TwindingCalc_MotorLAB                      = 65;       % Temperatures - Stator Winding Temperature - Calculation temperature
input.StatorCopperFreqCompTempExponent           = 1;        % Temperatures - Stator Winding Temperature - AC Loss Temperature Scailing - Temperature Exponent
input.TmagnetCalc_MotorLAB                       = 65;       % Temperatures - Magnet Temperature - Calculation temperature

% Elecromagnetic
input.EmagneticCalcType_Lab                     = 1;        % Calculation - Calculation Type : Efficiency Map
input.SmoothMap_MotorLAB                        = true;     % Calculation - Options - Smooth Map : "On"
input.PowerLim_MotorLAB                         = false;    % Calculation - Options - Power Limit : "Off"
if input.PowerLim_MotorLAB==true || input.PowerLim_MotorLAB==1
    input.PowerLimVal_MotorLAB                  = 1000000;  % Calculation - Options - Power Limit - Max Power
end
input.SpeedMax_MotorLAB                         = 30000;    % Calculation - Speed - Maximum
input.Speedinc_MotorLAB                         = 500;      % Calculation - Speed - Step Size
input.SpeedMin_MotorLAB                         = 500;      % Calculation - Speed - Minimum
input.Imax_MotorLAB                             = [];       %
input.Imax_RMS_MotorLAB                         = 500;      % Calculation - Current - Maximum (RMS)
input.Iinc_MotorLAB                             = 30;       % Calculation - Current - No. of Increments
input.Imin_MotorLAB                             = [];       %
input.Imin_RMS_MotorLAB                         = 0;       % Calculation - Current - Minimum (RMS)
input.TorqueMax_MotorLAB                        = [];       %
input.TorqueInc_MotorLAB                        = [];       %
input.MinTorque_MotorLAB                        = [];       %

%% 해석
% 전자계 해석 실행 & 결과 자동 저장 'MotorLAB_elecdata'
setMcadVariable(input,mcad);
% mcad.SetVariable("MessageDisplayState", 2);
mcad.CalculateMagnetic_Lab();

% 파일 복사
temp_data_file_path=fullfile(mcad_file_dir, mcad_file_name, 'Lab', 'MotorLAB_elecdata');
temp_time=clock;
data_file_path=[temp_data_file_path, '_', num2str(temp_time(4)), 'h', num2str(temp_time(5)), 'm'];
movefile([temp_data_file_path, '.mat'], [data_file_path, '.mat'])

% data 불러오기
data=load([data_file_path, '.mat']);

%% 계산
% BasePoint
data.DC_Bus_Voltage(1,1);
NumberOfIncrements=length(data.Voltage_Line_Peak(1,:));
MaximumVoltage=round(max(data.Voltage_Line_Peak(:,NumberOfIncrements)),0);
temp_BaseSpeedRow=min(find(round(data.Voltage_Line_Peak(:,NumberOfIncrements),0)==MaximumVoltage));

% BaseSpeed=data.Speed(BaseSpeedRow,NumberOfIncrements);
% BaseTorque=data.Shaft_Torque(BaseSpeedRow,NumberOfIncrements);
% MaximumPower=BaseTorque*BaseSpeed/60*2*pi;

VoltageSlope=(data.Voltage_Line_Peak(1,NumberOfIncrements)-data.Voltage_Line_Peak(temp_BaseSpeedRow-1,NumberOfIncrements))/...
    (data.Speed(1,NumberOfIncrements)-data.Speed(temp_BaseSpeedRow-1,NumberOfIncrements));
BaseSpeed_modified=(MaximumVoltage-data.Voltage_Line_Peak(1,NumberOfIncrements))/VoltageSlope+data.Speed(1,NumberOfIncrements);
TorqueSlope=(data.Shaft_Torque(1,NumberOfIncrements)-data.Shaft_Torque(temp_BaseSpeedRow-1,NumberOfIncrements))/...
    (data.Speed(1,NumberOfIncrements)-data.Speed(temp_BaseSpeedRow-1,NumberOfIncrements));
BaseTorque_modified=data.Shaft_Torque(1,NumberOfIncrements)-BaseSpeed_modified*TorqueSlope;
MaximumPower_modified=BaseTorque_modified*BaseSpeed_modified/60*2*pi;

% Maximum Speed
MaximumCurrent=round(max(data.Stator_Current_Phase_Peak(:,NumberOfIncrements)),0);
temp_FluxWeakeningRow=max(find(round(data.Stator_Current_Phase_Peak(:,NumberOfIncrements),0)==MaximumCurrent));

% FluxWeakeningSpeed=data.Speed(temp_FluxWeakeningRow,NumberOfIncrements);
% FluxWeakeningTorque=data.Shaft_Torque(temp_FluxWeakeningRow,NumberOfIncrements);

FluxWeakeningCurrentSlope=(data.Stator_Current_Phase_Peak(temp_FluxWeakeningRow+1,NumberOfIncrements)-data.Stator_Current_Phase_Peak(temp_FluxWeakeningRow+2,NumberOfIncrements))/...
    (data.Speed(temp_FluxWeakeningRow+1,NumberOfIncrements)-data.Speed(temp_FluxWeakeningRow+2,NumberOfIncrements));
FluxWeakeningSpeed_modified=(MaximumCurrent-data.Stator_Current_Phase_Peak(temp_FluxWeakeningRow+1,NumberOfIncrements))/FluxWeakeningCurrentSlope ...
    +data.Speed(temp_FluxWeakeningRow+1,NumberOfIncrements);
FluxWeakeningTorqueSlope=(data.Shaft_Torque(temp_FluxWeakeningRow+1,NumberOfIncrements)-data.Shaft_Torque(temp_FluxWeakeningRow+2,NumberOfIncrements))/ ...
    (data.Speed(temp_FluxWeakeningRow+1,NumberOfIncrements)-data.Speed(temp_FluxWeakeningRow+2,NumberOfIncrements));
FluxWeakeningTorque_modified=FluxWeakeningTorqueSlope*(FluxWeakeningSpeed_modified-data.Speed(temp_FluxWeakeningRow+1,NumberOfIncrements)) ...
    +data.Shaft_Torque(temp_FluxWeakeningRow+1,NumberOfIncrements);

if data.Shaft_Torque(length(data.Shaft_Torque(:,NumberOfIncrements)),NumberOfIncrements)>0
    MaximumSpeed=max(data.Speed(:,NumberOfIncrements));
else
    temp_MaxSpeedRow=min(find(round(data.Shaft_Torque(:,NumberOfIncrements),0)<=0));
    MaximumSpeed=data.Speed(temp_MaxSpeedRow-1,NumberOfIncrements);
end

% output
BasePointOutput=table2struct(table(MaximumPower_modified, BaseTorque_modified, BaseSpeed_modified, ...
    FluxWeakeningTorque_modified, FluxWeakeningSpeed_modified, MaximumSpeed));

end

