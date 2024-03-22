function T = setVarAsRowNames(T, varName)
    % 입력된 변수의 데이터 유형에 따라 테이블의 RowNames를 설정하는 범용 함수
    %
    % 입력:
    %   - T: 변환할 테이블
    %   - varName: RowNames로 설정할 변수의 이름 (문자열)
    %
    % 출력:
    %   - T: 업데이트된 테이블, RowNames가 설정됨

    % 입력된 변수의 데이터를 추출
    rowData = T.(varName);
    
    % 데이터 유형에 따라 적절하게 처리
    if isnumeric(rowData)
        % 숫자형 배열은 문자열 배열로 변환 후 셀 배열로 변환
        rowNames = cellstr(string(rowData));
    elseif iscell(rowData)
        % 셀 배열은 직접 사용
        rowNames = rowData;
    elseif isstring(rowData) || ischar(rowData)
        % 문자열 배열 또는 문자 배열은 셀 배열로 변환
        rowNames = cellstr(rowData);
    else
        error('Unsupported variable type for RowNames.');
    end
    
    % 변환된 데이터를 RowNames로 설정
    T.Properties.RowNames = rowNames;
end
