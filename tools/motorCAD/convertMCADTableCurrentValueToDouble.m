function mcadTable = convertMCADTableCurrentValueToDouble(mcadTable)
    % convertAndReorderCurrentValue - 'CurrentValue'를 double 형태로 변환하고 변수 위치 변경
    %
    % Inputs:
    %   ConductorLossTable - 'CurrentValue' 변수(셀 스트링 형태)를 포함한 원본 테이블
    %
    % Outputs:
    %   ConductorLossTable - 수정된 테이블 ('doubleValue' 변수 추가 및 위치 변경)

    % 'CurrentValue'의 각 셀 값을 숫자로 변환
    % doubleValues = cellfun(@(x) int2str(x), mcadTable.CurrentValue,'UniformOutput', false);
    doubleValues = cellfun(@(x) Convert2DoubleConditional(x), mcadTable.CurrentValue, 'UniformOutput', true);

    % doubleValues를 새 변수로 테이블에 추가
    if ~isvarofTable(mcadTable,'doubleValue')
    mcadTable.doubleValue = doubleValues;    
    else
    mcadTable.doubleValue = mcadTable.doubleValue;    
    end
    %% Nan이면 삭제하기
    % 'doubleValue'가 NaN인 행 찾기 및 삭제
    nanRows = isnan(mcadTable.doubleValue);
    mcadTable(nanRows, :) = [];
   
    %% 변수 순서 변경: 'doubleValue'를 'CurrentValue' 앞으로 이동
    % 변수 이름 목록 생성
    varNames = mcadTable.Properties.VariableNames;
    % 'doubleValue'의 인덱스 찾기
    doubleValueIndex = find(strcmp(varNames, 'doubleValue'));
    CurrentValueIndex = find(strcmp(varNames, 'CurrentValue'));

    % 위치 변환
    temp = varNames{doubleValueIndex};
    varNames{doubleValueIndex} = varNames{CurrentValueIndex};
    varNames{CurrentValueIndex} = temp;
    
    % 변수 순서를 업데이트하여 새로운 테이블 생성
    mcadTable = mcadTable(:, varNames);

    %% 오름차순정렬
    mcadTable = sortrows(mcadTable,"Number","ascend");
end
