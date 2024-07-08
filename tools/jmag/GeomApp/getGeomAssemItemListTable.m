function AssemTable = getGeomAssemItemListTable(geomApp,Type2filter)
    geomDocu  = geomApp.GetDocument;
    geomAssem = geomDocu.GetAssembly;

    % 테이블 초기화
    AssemCellList= [];
    if geomAssem.IsValid
        NumAssemItems = geomAssem.NumItems;

        for AssemItemIndex = 1:NumAssemItems
            tempItem = geomAssem.GetItem(int32(AssemItemIndex - 1));
            if tempItem.IsValid
                tempName = tempItem.GetName;
                tempType = tempItem.GetScriptTypeName;
            else
                continue; % 유효하지 않은 항목은 건너뜁니다.
            end

            if ~contains(tempName, 'Plane','IgnoreCase',true) && ~contains(tempName, 'Scale','IgnoreCase',true) 
                 newRow = {tempItem, tempName,tempType}; % 새 행 데이터
                % newRow = cell2table(newRow,'VariableNames');
                AssemCellList =[AssemCellList; newRow];
            end
        end
          AssemTable =cell2table(AssemCellList, 'VariableNames', {'AssemItem', 'AssemItemName','Type'});

    end
    
    %% Filter By Type
    if nargin>2
    AssemTable=AssemTable(contains(AssemTable.Type,Type2filter),:);
    end
end
