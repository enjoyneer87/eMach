function [Power, Torque, Speed] = MotorCAD_Lab_BasePoint(mcad, mcad_file_dir, mcad_file_name)

% 임시 
% mcad=actxserver('motorcad.appautomation');
% mcad_file_dir='E:\2023_Task\etc\14_EMLAB_TractionMotor\04_CODE\MCADSpary';
% mcad_file_name='Model1e2Spray2023';
% data=load('E:\2023_Task\etc\14_EMLAB_TractionMotor\04_CODE\MCADSpary\Model1e2Spray2023\Lab\MotorLAB_elecdata_copy.mat');

%% 셋팅
% 전자계 해석 실행 & 결과 자동 저장 'MotorLAB_elecdata'
mcad.CalculateMagnetic_Lab();

% 파일 복사
temp_data_file_path=fullfile(mcad_file_dir, mcad_file_name, 'Lab', 'MotorLAB_elecdata');
temp_time=clock;
data_file_path=[temp_data_file_path, '_', num2str(temp_time(4)), 'h', num2str(temp_time(5)), 'm'];
movefile([temp_data_file_path, '.mat'], [data_file_path, '.mat'])

% data 불러오기
data=load([data_file_path, '.mat']);

%% 계산
data.DC_Bus_Voltage(1,1);
NumberOfIncrements=length(data.Voltage_Line_Peak(1,:));
MaximumVoltage=round(max(data.Voltage_Line_Peak(:,NumberOfIncrements)),0);
BaseSpeedRow=min(find(round(data.Voltage_Line_Peak(:,NumberOfIncrements),0)==MaximumVoltage));

% BaseSpeed=data.Speed(BaseSpeedRow,NumberOfIncrements);
% BaseTorque=data.Shaft_Torque(BaseSpeedRow,NumberOfIncrements);
% MaximumPower=BaseTorque*BaseSpeed/60*2*pi;

VoltageSlope=(data.Voltage_Line_Peak(1,NumberOfIncrements)-data.Voltage_Line_Peak(BaseSpeedRow-1,NumberOfIncrements))/...
    (data.Speed(1,NumberOfIncrements)-data.Speed(BaseSpeedRow-1,NumberOfIncrements));
BaseSpeed_modified=(MaximumVoltage-data.Voltage_Line_Peak(1,NumberOfIncrements))/VoltageSlope+data.Speed(1,NumberOfIncrements);
TorqueSlope=(data.Shaft_Torque(1,NumberOfIncrements)-data.Shaft_Torque(BaseSpeedRow-1,NumberOfIncrements))/...
    (data.Speed(1,NumberOfIncrements)-data.Speed(BaseSpeedRow-1,NumberOfIncrements));
BaseTorque_modified=data.Shaft_Torque(1,NumberOfIncrements)-BaseSpeed_modified*TorqueSlope;
MaximumPower_modified=BaseTorque_modified*BaseSpeed_modified/60*2*pi;

Power=MaximumPower_modified;
Torque=BaseTorque_modified;
Speed=BaseSpeed_modified;

end

