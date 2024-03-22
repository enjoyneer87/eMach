function output = Convert2DoubleConditional(x)
    % 각 셀의 데이터 타입에 따라 조건적으로 처리
    if ischar(x)  % 문자열인 경우
        output = convertCharsToStrings(x);
        output = str2double(output);
    elseif isstring(x)
        output = str2double(x);
    elseif isnumeric(x)  % 숫자형인 경우 (MATLAB에서 모든 숫자는 기본적으로 double이지만, 예제의 목적을 위해)
        output = double(x);  % 명시적으로 double 형태로 변환
    else  % 그 외의 데이터 타입인 경우
        output = NaN;  % 변환할 수 없음을 나타내기 위해 NaN 사용
    end
end
