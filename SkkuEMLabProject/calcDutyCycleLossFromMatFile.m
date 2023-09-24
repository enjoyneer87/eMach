 
function DutyCycleOutput=calcDutyCycleLossFromMatFile(driveMatPath)
    if contains(driveMatPath,'.mat')
    matData                 = load(driveMatPath);
    else
    matData                 = load(strcat(driveMatPath),'mat');
    end


%% 계산
    % 전자계 토크 무의미
    % 효율 = 샤프트 토크 / (샤프트 토크 + 토탈 로스)
    % 터미널 파워 = 샤프트 토크 / 효율 = 샤프트 토크 + 토탈 로스
    % 드라이빙 사이클 파워 = ? / 역률 아님, 가속 아님
    % 파워 팩터 미사용 ?
    secondsInHour=3600;
    SumOfTerminalPower=sum(matData.Terminal_Power)/secondsInHour;
    PositiveSumOfTerminalPower=0;
    
    % Terminal Power
    for j=1:length(matData.Terminal_Power(:,1))
        if matData.Terminal_Power(j,1)>0
            PositiveSumOfTerminalPower=PositiveSumOfTerminalPower+matData.Terminal_Power(j,1);
        end
    end

    TimeStep=matData.Time(end-1)-matData.Time(end-2);    
    % Shaft Power

    % DriveCyclePower
    SumofDriveCyclePower=sum(matData.Drive_Cycle_Power)*TimeStep/secondsInHour;
    PositiveSumOfDriveCyclePower=0;
    for j=1:length(matData.Drive_Cycle_Power(:,1))
        if matData.Drive_Cycle_Power(j,1)>0
            PositiveSumOfDriveCyclePower=PositiveSumOfDriveCyclePower+matData.Drive_Cycle_Power(j,1);
        end
    end
    
    SumofTotalLoss=sum(matData.Total_Loss)*TimeStep/secondsInHour;
    
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
    
    DutyCycleOutput=table2struct(table(SumOfTerminalPower, PositiveSumOfTerminalPower, SumofTotalLoss, ...
        SumOfApparentPower, PositiveSumOfApparentPower));
    % DutyCycleOutput.ShaftPower=data.Shaft_Power;
    DutyCycleOutput.ShaftTorque=matData.Shaft_Torque;
    DutyCycleOutput.Speed=matData.Speed;
    DutyCycleOutput.matData=matData;

    end