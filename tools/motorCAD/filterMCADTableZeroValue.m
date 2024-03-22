function updatedTable = filterMCADTableZeroValue(McadTable)
    % removeZeroRowsSimple - 'CurrentValue'의 값이 '0' 또는 모든 값이 '0'인 행을 삭제
    %
    % Inputs:
    %   McadWattsTable - 'CurrentValue' 변수를 포함한 원본 테이블
    %
    % Outputs:
    %   updatedTable - 수정된 테이블

    % 'CurrentValue'의 값이 '0' 또는 모든 값이 '0'인 행 찾기
    isNotZeroRow = false(height(McadTable), 1); % 모든 행을 'false'로 초기화

    for i = 1:height(McadTable)
        currentValue = McadTable.CurrentValue{i};
        % if isstring(currentValue)
            if strcmp(currentValue, '0')
                % 'CurrentValue'가 '0'인 경우
                continue; % 이 행을 삭제 대상으로 표시하지 않음
            else
                % '0 : 0 : 0 : 0 : 0' 형태인지 확인
                splittedValues = strsplit(currentValue, ':'); % ':'로 분할
                allZeros = all(cellfun(@(x) strcmp(strtrim(x), '0'), splittedValues));
                if ~allZeros
                    isNotZeroRow(i) = true; % 이 행은 삭제 대상이 아님
                end
            end
        % end
    end

    % 해당하는 행 삭제
    updatedTable = McadTable(isNotZeroRow, :);
end
