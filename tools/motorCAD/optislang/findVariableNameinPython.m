function pythonSetVariableName = findVariableNameinPython(matchedPythonLines, MotorCADSetVariableName)
% setVariable로 입력된 값 (숫자, 변수명 포함)
    % 검색할 문자열 패턴
pattern = '(?<=,).*?(?=\))';
    % MotorCADSetvariableName 문자열이 저장된 셀 배열
    % MotorCADSetvariableName에 해당하는 문자열만 추출
pythonSetVariableName = {};
for i = 1:numel(matchedPythonLines)
    if contains(matchedPythonLines{i}, MotorCADSetVariableName{i})
        result = regexp(matchedPythonLines{i}, pattern, 'match');
        pythonSetVariableName = [pythonSetVariableName, result];
    else
        pythonSetVariableName = [pythonSetVariableName, {''}];
    end
end
pythonSetVariableName=strtrim(pythonSetVariableName)

end