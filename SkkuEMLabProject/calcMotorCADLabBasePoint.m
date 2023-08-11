function BasePointOutput = calcMotorCADLabBasePoint(mcad, mcad_file_dir, mcad_file_name, input)

% 임시 
% mcad=actxserver('motorcad.appautomation');
% mcad_file_dir='E:\2023_Task\etc\14_EMLAB_TractionMotor\04_CODE\MCADSpary';
% mcad_file_name='Model1e2Spray2023';
% data=load('E:\2023_Task\etc\14_EMLAB_TractionMotor\04_CODE\MCADSpary\Model1e2Spray2023\Lab\MotorLAB_elecdata_copy.mat');

% LoadFromFile
motFile=strcat(mcad_file_name,'.mot');
motFilePath=fullfile(mcad_file_dir,motFile);
mcad.LoadFromFile(motFilePath);
%% 해석
% 전자계 해석 실행 & 결과 자동 저장 'MotorLAB_elecdata'
% setMcadVariable(input,mcad);
setMcadTableVariable(input,mcad);
mcad.SetVariable("MessageDisplayState", 2);
mcad.CalculateMagnetic_Lab();
% 저장
mcad.SaveToFile(motFilePath);

% 파일 복사
initialMatFileDir=fullfile(mcad_file_dir, mcad_file_name, 'Lab', 'MotorLAB_elecdata');
temp_time=datetime("now");
matFileDir=strcat(initialMatFileDir, '_', num2str(temp_time.Hour), 'h', num2str(temp_time.Minute), 'm');
movefile(strcat(initialMatFileDir, '.mat'), strcat(matFileDir, '.mat'));

% data 불러오기
matData=load(strcat(matFileDir, '.mat'));

%% 계산
matData.DC_Bus_Voltage(1,1);
NumberOfIncrements=length(matData.Voltage_Line_Peak(1,:));
MaximumVoltage=round(max(matData.Voltage_Line_Peak(:,NumberOfIncrements)),0);
BaseSpeedRow=min(find(round(matData.Voltage_Line_Peak(:,NumberOfIncrements),0)==MaximumVoltage));

% BaseSpeed=data.Speed(BaseSpeedRow,NumberOfIncrements);
% BaseTorque=data.Shaft_Torque(BaseSpeedRow,NumberOfIncrements);
% MaximumPower=BaseTorque*BaseSpeed/60*2*pi;

VoltageSlope=(matData.Voltage_Line_Peak(1,NumberOfIncrements)-matData.Voltage_Line_Peak(BaseSpeedRow-1,NumberOfIncrements))/...
    (matData.Speed(1,NumberOfIncrements)-matData.Speed(BaseSpeedRow-1,NumberOfIncrements));
BaseSpeed_modified=(MaximumVoltage-matData.Voltage_Line_Peak(1,NumberOfIncrements))/VoltageSlope+matData.Speed(1,NumberOfIncrements);
TorqueSlope=(matData.Shaft_Torque(1,NumberOfIncrements)-matData.Shaft_Torque(BaseSpeedRow-1,NumberOfIncrements))/...
    (matData.Speed(1,NumberOfIncrements)-matData.Speed(BaseSpeedRow-1,NumberOfIncrements));
BaseTorque_modified=matData.Shaft_Torque(1,NumberOfIncrements)-BaseSpeed_modified*TorqueSlope;
MaximumPower_modified=BaseTorque_modified*BaseSpeed_modified/60*2*pi;

%% [TC]Return
BasePointOutput=table2struct(table(MaximumPower_modified, BaseTorque_modified, BaseSpeed_modified));
BasePointOutput.matData=matData;
BasePointOutput.matFileDir=matFileDir;
BasePointOutput.matFilePath=strcat(matFileDir, '.mat');

end

