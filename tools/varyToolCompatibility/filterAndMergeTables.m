function mergedTable = filterAndMergeTables(changedOriginalTable, LabLinkFormatNameCell, MachineData)
    % changedOriginalTable에서 LabLinkFormat에 있는 변수만 남기고 AC Copper Loss를 계산하여 합치는 함수

    % 변수 이름 가져오기
    varNames = changedOriginalTable.Properties.VariableNames;

    % 변수 필터링
    varToKeep = intersect(varNames, LabLinkFormatNameCell);
    filteredTable = changedOriginalTable(:, varToKeep);

    % AC Copper Loss 변수 및 데이터 가져오기
    ACIndex = contains(LabLinkFormatNameCell, 'AC Copper');
    ACNameCell = LabLinkFormatNameCell(ACIndex);
    ACConductorLossProportion_Lab = convertCharTypeData2ArrayData(MachineData.ACConductorLossProportion_Lab);

    % AC Copper Loss 계산 및 테이블 생성
    numACLossVariables = numel(ACNameCell);
    ACLossTable = array2table(zeros(size(changedOriginalTable, 1), numACLossVariables), 'VariableNames', ACNameCell);

    for i = 1:numACLossVariables
        ACVarName = ACNameCell{i};
        ACLossTable{:, ACVarName} = changedOriginalTable{:, 'Stator Copper Loss AC'} .* ACConductorLossProportion_Lab(i, :);
    end

    % 두 테이블 합치기
    mergedTable = [filteredTable, ACLossTable];
end
