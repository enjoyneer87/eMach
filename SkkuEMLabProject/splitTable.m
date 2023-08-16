function tables = splitTable(dividedMotorCurve)
    % 테이블의 변수 이름 가져오기
    variableNames = dividedMotorCurve.Properties.VariableNames;

    % 결과를 저장할 빈 셀 배열 생성
    tables = cell(1, 3);

    for i = 1:3
        % 새로운 테이블 생성
        newTable = table();

        % 모든 변수를 순회하며 분할
        for varName = variableNames
            varName = varName{1};
            data = dividedMotorCurve.(varName);
            if size(data, 2) == 3
                % 36x3 배열인 경우 분할
                newTable.(varName) = data(:, i);
            elseif size(data, 2) == 1
                % 36x1 배열인 경우 그대로 복사
                newTable.(varName) = data;
            else
                error('예상치 못한 변수 크기');
            end
        end

        % 결과 저장
        tables{i} = newTable;
    end
end
