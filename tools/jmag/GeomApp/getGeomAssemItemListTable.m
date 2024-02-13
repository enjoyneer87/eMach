function AssemTable = getGeomAssemItemListTable(geomApp)
    geomDocu = geomApp.GetDocument;
    geomAssem = geomDocu.GetAssembly;

    % 테이블 초기화
    AssemTable = table([], {}, 'VariableNames', {'AssemItem', 'AssemItemName'});

    if geomAssem.IsValid
        NumAssemItems = geomAssem.NumItems;

        for AssemItemIndex = 1:NumAssemItems
            tempItem = geomAssem.GetItem(int32(AssemItemIndex - 1));
            if tempItem.IsValid
                tempName = tempItem.GetName;
            else
                continue; % 유효하지 않은 항목은 건너뜁니다.
            end

            if ~contains(tempName, 'Plane')
                newRow = {tempItem, tempName}; % 새 행 데이터
                AssemTable = [AssemTable; newRow]; % 테이블에 행 추가
            end
        end
    end
end
