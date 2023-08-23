function DutyCycleOutput = calcMotorCADLabDutyCycle(mcad, mcad_file_dir, mcad_file_name, input)

% 임시 
% mcad=actxserver('motorcad.appautomation');
% mcad_file_dir='E:\2023_Task\etc\14_EMLAB_TractionMotor\04_CODE\MCADSpary';
% mcad_file_name='Model1e2Spray2023';
% data=load('E:\2023_Task\etc\14_EMLAB_TractionMotor\04_CODE\MCADSpary\Model1e2Spray2023\Lab\MotorLAB_elecdata_copy.mat');

%% 셋팅

%% 입력데이터 설정
setMcadTableVariable(input, mcad);


%% 해석
% duty cycle 해석 실행 & 결과 자동 저장 'MotorLAB_drivecycledata'
mcad.SetVariable("MessageDisplayState", 2);
mcad.CalculateDutyCycle_Lab();

%% 결과 파일 복사 및 로드
initialMatFileDir       = fullfile(mcad_file_dir, mcad_file_name, 'Lab', 'MotorLAB_drivecycledata');
if exist(initialMatFileDir,"file")
    temp_time               = datetime("now");
    matFileDir              = strcat(initialMatFileDir, '_', num2str(temp_time.Hour), 'h', num2str(temp_time.Minute), 'm');    
    movefile(strcat(initialMatFileDir, '.mat'), strcat(matFileDir, '.mat'));
else
    matFileDir=[];
end
if ~isempty(matFileDir)||exist(matFileDir,"file")
    matData                 = load(strcat(matFileDir, '.mat'));
else
    matData                 = load(strcat(initialMatFileDir,'.mat'));
end
%% 계산
    % 전자계 토크 무의미
    % 효율 = 샤프트 토크 / (샤프트 토크 + 토탈 로스)
    % 터미널 파워 = 샤프트 토크 / 효율 = 샤프트 토크 + 토탈 로스
    % 드라이빙 사이클 파워 = ? / 역률 아님, 가속 아님
    % 파워 팩터 미사용 ?
    SumOfTerminalPower=sum(matData.Terminal_Power);
    PositiveSumOfTerminalPower=0;
    for j=1:length(matData.Terminal_Power(:,1))
        if matData.Terminal_Power(j,1)>0
            PositiveSumOfTerminalPower=PositiveSumOfTerminalPower+matData.Terminal_Power(j,1);
        end
    end
    TimeStep=matData.Time(end-1)-matData.Time(end-2);    

    SumOfDriveCyclePower=sum(matData.Drive_Cycle_Power)*TimeStep;
    PositiveSumOfDriveCyclePower=0;
    for j=1:length(matData.Drive_Cycle_Power(:,1))
        if matData.Drive_Cycle_Power(j,1)>0
            PositiveSumOfDriveCyclePower=PositiveSumOfDriveCyclePower+matData.Drive_Cycle_Power(j,1);
        end
    end
    
    SumOfTotalLoss=sum(matData.Total_Loss)*TimeStep;
    EnergyConsumptioninWh=SumOfTotalLoss/3600;
    ApparentPower=matData.Terminal_Power./matData.Power_Factor;
    SumOfApparentPower=0;
    for j=1:length(ApparentPower)
        if ApparentPower(j,1)~=Inf
            SumOfApparentPower=SumOfApparentPower+ApparentPower(j,1);
        end
    end
    PositiveSumOfApparentPower=0;
    for j=1:length(ApparentPower)
        if ApparentPower(j,1)~=Inf && ApparentPower(j,1)>0
            PositiveSumOfApparentPower=PositiveSumOfApparentPower+ApparentPower(j,1);
        end
    end
    
    DutyCycleOutput=table2struct(table(SumOfTerminalPower, PositiveSumOfTerminalPower, SumOfTotalLoss, ...
        SumOfApparentPower, PositiveSumOfApparentPower));
    % DutyCycleOutput.ShaftPower=data.Shaft_Power;
    DutyCycleOutput.ShaftTorque=matData.Shaft_Torque;
    DutyCycleOutput.Speed=matData.Speed;
    DutyCycleOutput.matData=matData;
    DutyCycleOutput.EnergyConsumptioninWh;
end
