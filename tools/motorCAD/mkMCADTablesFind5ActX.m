function mergedTable = mkMCADTablesFind5ActX(settingTable)
% 5(Five) = From
    MCADStruct=defMcadTableStruct();
    % 합칠 테이블을 초기화합니다.
    mergedTable = table();

    % refDriveSettingTable의 각 행을 반복 처리합니다.
    for idx = 1:height(settingTable)
        % AutomationName으로 필터링 함수를 호출합니다.
        automationName = settingTable.AutomationName{idx};
        [filteredTable, ~] = findAutomationNameFromAllCategory(MCADStruct, automationName);
        
        % filteredTable이 비어 있지 않은 경우 처리합니다.
        if ~isempty(filteredTable)
            % CurrentValue 업데이트
            % filteredTable.CurrentValue(:) = refDriveSettingTable.CurrentValue(idx);
            if iscell(settingTable.CurrentValue)
            filteredTable = updateMcadTableVariable(filteredTable, automationName, settingTable.CurrentValue{idx});
            else
            filteredTable = updateMcadTableVariable(filteredTable, automationName, settingTable.CurrentValue(idx));
            end
            % 결과 테이블에 추가합니다.
            mergedTable = [mergedTable; filteredTable];  % vertcat 함수를 사용하여 테이블을 수직으로 합칩니다.
        end
    end
    %반환
    return
end