function BasePointOutput = calcMotorCADLabBasePoint(mcad, mcad_file_dir, mcad_file_name, input)
    % MotorCADLab 기반 점 계산 함수
    %
    % 이 함수는 MotorCADLab 소프트웨어를 사용하여 전자기 해석을 수행하고, 해당 결과를 기반으로 트랙션 모터의 기반 점을 계산합니다.
    %
    % 매개변수:
    % mcad: MotorCADLab Automation 객체
    % mcad_file_dir: MotorCAD 파일 디렉토리 경로
    % mcad_file_name: MotorCAD 파일 이름 (확장자 제외)
    % input: 입력 데이터 구조체
    %
    % 반환값:
    % BasePointOutput: 기반 점 계산 결과 구조체

    % MotorCADLab 서버 연결 및 초기 설정
    % mcad=actxserver('motorcad.appautomation');
    % mcad_file_dir='E:\2023_Task\etc\14_EMLAB_TractionMotor\04_CODE\MCADSpary';
    % mcad_file_name='Model1e2Spray2023';
    % matData=load('E:\2023_Task\etc\14_EMLAB_TractionMotor\04_CODE\MCADSpary\Model1e2Spray2023\Lab\MotorLAB_elecdata_copy.mat');
    
    % 파일 경로 설정 및 로드
    motFile                 = strcat(mcad_file_name, '.mot');
    motFilePath             = fullfile(mcad_file_dir, motFile);
    mcad.LoadFromFile(motFilePath); % 임시
    
    %% 전자기 해석 실행
    % 입력 데이터 설정
    % setMcadVariable(input, mcad);
    setMcadTableVariable(input, mcad);
    
    % 해석 실행 및 결과 저장
    mcad.SetVariable("MessageDisplayState", 2);
    mcad.CalculateMagnetic_Lab();
    % 파일 저장
    mcad.SaveToFile(motFilePath);  % 임시
    
    % 결과 파일 복사 및 로드
    initialMatFileDir       = fullfile(mcad_file_dir, mcad_file_name, 'Lab', 'MotorLAB_elecdata');
    temp_time               = datetime("now");
    matFileDir              = strcat(initialMatFileDir, '_', num2str(temp_time.Hour), 'h', num2str(temp_time.Minute), 'm');
    
    movefile(strcat(initialMatFileDir, '.mat'), strcat(matFileDir, '.mat'));
    matData                 = load(strcat(matFileDir, '.mat'));
    
    %% BasePoint  계산
    matData.DC_Bus_Voltage(1, 1);
    NumberOfIncrements      = length(matData.Voltage_Line_Peak(1, :));
    
    % 전압과 속도 관련 계산
    MaximumVoltage          = round(max(matData.Voltage_Line_Peak(:, NumberOfIncrements)), 0);
    BaseSpeedRow = min(find(round(matData.Voltage_Line_Peak(:, NumberOfIncrements), 0) == MaximumVoltage));
    VoltageSlope = (matData.Voltage_Line_Peak(1, NumberOfIncrements) - matData.Voltage_Line_Peak(BaseSpeedRow - 1, NumberOfIncrements)) / ...
        (matData.Speed(1, NumberOfIncrements) - matData.Speed(BaseSpeedRow - 1, NumberOfIncrements));
    BaseSpeed_modified = (MaximumVoltage - matData.Voltage_Line_Peak(1, NumberOfIncrements)) / VoltageSlope + matData.Speed(1, NumberOfIncrements);
    TorqueSlope = (matData.Shaft_Torque(1, NumberOfIncrements) - matData.Shaft_Torque(BaseSpeedRow - 1, NumberOfIncrements)) / ...
        (matData.Speed(1, NumberOfIncrements) - matData.Speed(BaseSpeedRow - 1, NumberOfIncrements));
    BaseTorque_modified = matData.Shaft_Torque(1, NumberOfIncrements) - BaseSpeed_modified * TorqueSlope;
    MaximumPower_modified = BaseTorque_modified * BaseSpeed_modified / 60 * 2 * pi;
    
    % 최대 속도 관련 계산
    MaximumCurrent = round(max(matData.Stator_Current_Phase_Peak(:, NumberOfIncrements)), 0);
    temp_FluxWeakeningRow = max(find(round(matData.Stator_Current_Phase_Peak(:, NumberOfIncrements), 0) == MaximumCurrent));
    FluxWeakeningCurrentSlope = (matData.Stator_Current_Phase_Peak(temp_FluxWeakeningRow + 1, NumberOfIncrements) - matData.Stator_Current_Phase_Peak(temp_FluxWeakeningRow + 2, NumberOfIncrements)) / ...
        (matData.Speed(temp_FluxWeakeningRow + 1, NumberOfIncrements) - matData.Speed(temp_FluxWeakeningRow + 2, NumberOfIncrements));
    FluxWeakeningSpeed_modified = (MaximumCurrent - matData.Stator_Current_Phase_Peak(temp_FluxWeakeningRow + 1, NumberOfIncrements)) / FluxWeakeningCurrentSlope ...
        + matData.Speed(temp_FluxWeakeningRow + 1, NumberOfIncrements);
    FluxWeakeningTorqueSlope = (matData.Shaft_Torque(temp_FluxWeakeningRow + 1, NumberOfIncrements) - matData.Shaft_Torque(temp_FluxWeakeningRow + 2, NumberOfIncrements)) / ...
        (matData.Speed(temp_FluxWeakeningRow + 1, NumberOfIncrements) - matData.Speed(temp_FluxWeakeningRow + 2, NumberOfIncrements));
    FluxWeakeningTorque_modified = FluxWeakeningTorqueSlope * (FluxWeakeningSpeed_modified - matData.Speed(temp_FluxWeakeningRow + 1, NumberOfIncrements)) ...
        + matData.Shaft_Torque(temp_FluxWeakeningRow + 1, NumberOfIncrements);
    
    if matData.Shaft_Torque(length(matData.Shaft_Torque(:, NumberOfIncrements)), NumberOfIncrements) > 0
        MaximumSpeed = max(matData.Speed(:, NumberOfIncrements));
    else
        temp_MaxSpeedRow = min(find(round(matData.Shaft_Torque(:, NumberOfIncrements), 0) <= 0));
        MaximumSpeed = matData.Speed(temp_MaxSpeedRow - 1, NumberOfIncrements);
    end
    
    %% Return
    BasePointOutput = table2struct(table(MaximumPower_modified, BaseTorque_modified, BaseSpeed_modified, ...
        FluxWeakeningTorque_modified, FluxWeakeningSpeed_modified, MaximumSpeed));
    
    BasePointOutput.matFilePath     = strcat(matFileDir, '.mat');
    BasePointOutput.matData         = matData;
    BasePointOutput.matFileDir      = matFileDir;
end
