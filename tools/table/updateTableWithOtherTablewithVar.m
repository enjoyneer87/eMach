function targetTable = updateTableWithOtherTablewithVar(sourceTable, targetTable, VarName)
    % sourceTable: 값을 가져올 테이블
    % targetTable: 값을 대입할 테이블
    % sourceVarName: sourceTable의 변수 이름
    % targetVarName: targetTable의 변수 이름

    % 'Id' 변수가 같은 행 찾기
    [~, sourceIdx, targetIdx] = intersect(sourceTable.(VarName), targetTable.(VarName));

    % 값 대입
    targetTable(targetIdx,:) = sourceTable(sourceIdx,:);
end
