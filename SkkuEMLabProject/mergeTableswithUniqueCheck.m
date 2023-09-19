function mergedTable = mergeTableswithUniqueCheck(table1, table2)
    % 테이블 크기 확인
    [rows1, cols1] = size(table1);
    [rows2, cols2] = size(table2);
    
    % 변수 이름 추출
    varNames1 = table1.Properties.VariableNames;
    varNames2 = table2.Properties.VariableNames;
    
    % 공통 변수 이름 찾기
    commonVarNames = intersect(varNames1, varNames2);
    
    % 공통 변수가 없을 경우 처리
    if isempty(commonVarNames)
        error('공통 변수가 없습니다.');
    end
    
    % 합칠 행 찾기
    % matchingRows = ismember(table1(:, commonVarNames), table2(:, commonVarNames));
    
    % 행 인덱스 추출
    % matchingIndices = find(any(matchingRows, 2));
    
    % 행 합치기
    % mergedTable = [table1(matchingIndices, :), table2(matchingIndices, :)];
    %% 두테이블 합치기
    mergedTable = [table1; table2];
end
