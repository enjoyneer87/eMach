mcApp = actxserver('MotorCAD.AppAutomation');

%% ReadTable
path='DirectOpti_HDEV_low_fidelity_designTable.csv'
directDesigntable=readtable(path);

%% Variable Name 
VariableNamesCSV=directDesigntable.Properties.VariableNames;

%% Find inputVariableName 
strings_to_find = {'o_', 'obj_', 'constr'};
inputVariableNames=autoVariableFindFromCell(VariableNamesCSV,strings_to_find);

% directDesigntable.Properties.VariableNames cell 배열에서 inputVariableNames cell 배열과 일치하는 원소의 인덱스 찾기
[~, idx] = ismember(inputVariableNames, directDesigntable.Properties.VariableNames);
csvVariableData = directDesigntable(:, idx);
%% Match with MotorCAD Variable Names (Manually)
% 코드에서 setVariable로 사용된 변수이름
python_file_path = 'Z:\Thesis\Optislang_Motorcad\HDEV_Code3\PYTHON\HDEV_ob2o23i23si1f1.py';
search_string='SetVariable('
afterstring = 'SetVariable('
[matchedPythonLines, mcadCode] = findCodePythonContainStr(python_file_path, search_string);

%% Set Array
search_string='SetArrayVariable('
[matchedPythonLines, mcadCodeArrayVariable] = findCodePythonContainStr(python_file_path, search_string);


%%
ResultCsvVariableData=csvVariableData;
ResultCsvVariableData.Weight_Act=zeros(height(ResultCsvVariableData),1);
ResultCsvVariableData.o_Wh_Loss=zeros(height(ResultCsvVariableData),1);


Thermal_CouplingType=2;
% Thermal_CouplingType=2;

for csvCaseIndex=height(csvVariableData)-20:height(csvVariableData)
    mcadShouldCode=makeCellofExcuteCode(csvVariableData, mcadCode, inputVariableNames,csvCaseIndex);
    mcadShouldCode=strrep(mcadShouldCode, 'np.', '')
    mcadShouldCodeArrayVariable=makeCellofExcuteCode(csvVariableData, mcadCodeArrayVariable, inputVariableNames,csvCaseIndex);
    mcadShouldCodeArrayVariable=strrep(mcadShouldCodeArrayVariable, 'np.', '')
    
    for i=1:numel(mcadShouldCode)
        disp(mcadShouldCode{i})
        eval(mcadShouldCode{i})
    end
    for i=1:numel(mcadShouldCodeArrayVariable)
        disp(mcadShouldCodeArrayVariable{i})
        eval(mcadShouldCodeArrayVariable{i})
    end
    mcApp.DoWeightCalculation()                                            
    [ex, ResultCsvVariableData.Weight_Act(csvCaseIndex)]         = mcApp.GetVariable("Weight_Calc_Total")        
    mcApp.BuildModel_Lab()       

    M1 = {'M1_Nosync', 'M1'};
    ext_Duty_Cycle=M1
    Design_Name= "HDEV_Model2"  
    OSL_PROJECT_DIR='Z:\Thesis\Optislang_Motorcad\HDEV_Code3f3\OPD\HDEVCODE3f3.opd'
%     ResultCsvVariableData.o_Wh_Loss(csvCaseIndex) = funDrivingDuty(M1,OSL_PROJECT_DIR)
    ref_Duty_Cycle = fullfile(fileparts(fileparts(OSL_PROJECT_DIR)), 'DutyCycleData', strcat(ext_Duty_Cycle{1}, '.dat'));

    mcApp.LoadDutyCycle(ref_Duty_Cycle)
%     mcApp.SetVariable('TurnsCalc_MotorLAB', turns)           
    mcApp.SetVariable("LabThermalCoupling_DutyCycle", Thermal_CouplingType)     
    mcApp.SetVariable("LabThermalCoupling", 0)               
    mcApp.SetVariable('InitialTransientTemperatureOption',4)
    mcApp.SetVariable('InitialHousingTemperature',65)
    mcApp.SetVariable('InitialHousingTemperature',65)
    mcApp.SetVariable('InitialStatorTemperature',65)
    mcApp.SetVariable('InitialWindingTemperature',65)
    mcApp.SetVariable('InitialRotorTemperature',65)
    mcApp.SetVariable('InitialMagnetTemperature',65)
    mcApp.CalculateDutyCycle_Lab()
%      Calculation & Post processing
    [ex, ResultCsvVariableData.o_Wh_Loss(csvCaseIndex)]  = mcApp.GetVariable("DutyCycleTotalLoss")   
%     ex, o_Wh_Shaft = mcApp.GetVariable("DutyCycleTotalEnergy_Shaft_Output")   
%     ex, o_Wh_input = mcApp.GetVariable("DutyCycleTotalEnergy_Electrical_Input")  

end


MotorCADSetVariableName = findVariableNameMotorCADfcn(matchedPythonLines,afterstring);


inputVariableNames

% setVariable로 입력된 값 (숫자, 변수명 포함)
pythonSetVariableData = findVariableNameinPython(matchedPythonLines, MotorCADSetVariableName);
% 결과 출력
length(MotorCADSetVariableName)
length(pythonSetVariableData)
combinedCellVariable = vertcat(MotorCADSetVariableName, pythonSetVariableData);

% 변수 이름과 csv에 포함되어있는 일치하는 문자열 추출
matchedWithCSVFileVariable=findMatchedCell(VariableNamesCSV,combinedCellVariable);
matchedWithCSVFileVariable=strtrim(matchedWithCSVFileVariable)
%% setArrayVariable
% 코드에서 setVariable로 사용된 변수이름
search_string='SetArrayVariable('
afterstring='SetArrayVariable('
matchedPythonLines2 = findCodePythonContainStr(python_file_path, search_string)
MotorCADSetArrayVariableName = findVariableNameMotorCADfcn(matchedPythonLines2,afterstring);
% setVariable로 입력된 값 (숫자, 변수명 포함)
pythonSetArrayVariableName = findVariableNameinPython(matchedPythonLines2, MotorCADSetArrayVariableName);





csvVariableData = directDesigntable(:, idx);


% 결과 출력
length(MotorCADSetArrayVariableName)
length(pythonSetArrayVariableName)
combinedCellArrayVariable = vertcat(MotorCADSetArrayVariableName, pythonSetArrayVariableName);

% 변수 이름과 csv에 포함되어있는 일치하는 문자열 추출
matchedWithCSVFileArrayVariable=findMatchedCell(VariableNamesCSV,combinedCellArrayVariable);

% 결과 출력

%%
mcad = actxserver('MotorCAD.AppAutomation');


%% 
% inputVariableNames에서 변수 이름을 찾고자 하는 문자열
% 파이썬 코드 파일 경로

% inputVariableNames의 각 셀에서 변수 이름 추출
variable_names = {};


    % 결과 저장



% 결과 출력
disp('추출된 변수 이름:');
for i = 1:numel(variable_names)
    if isempty(variable_names{i})
        disp(['Variable "', inputVariableNames{i}, '"에서 변수 이름을 찾을 수 없습니다.']);
    else
        disp(['Variable "', inputVariableNames{i}, '"의 변수 이름은 "', variable_names{i}, '"입니다.']);
    end
end
