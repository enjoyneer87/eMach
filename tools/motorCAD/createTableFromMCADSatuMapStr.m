function [dataTable,otherStruct] = createTableFromMCADSatuMapStr(buildData)
    hasSpecifiedTypeField = checkForSpecifiedTypeFields(buildData, 'struct');
    
    if hasSpecifiedTypeField==1
        satuMapData= buildData.satuMapData;
    else
        satuMapData =buildData;
    end
        

    % SatuMapData 구조체에서 varStr 필드의 문자열 가져오기
    targetStr = cellstr(satuMapData.varStr);

    % SatuMapData 구조체에서 varUnit 필드의 정보 가져오기
    unitInfo = cellstr(satuMapData.varUnits);

    % 결과를 저장할 테이블을 초기화합니다.
    dataTable = table();

    % SatuMapData 구조체의 모든 필드에 대해 반복합니다.
    fields = fieldnames(satuMapData);    
    for i = 1:numel(fields)
        % 현재 필드의 이름을 가져옵니다.
        fieldName = fields{i};

        % 현재 필드의 값 가져오기
        fieldValue = satuMapData.(fieldName);

        % 현재 필드의 이름이 varStr 문자열 배열에 있는 경우만 처리합니다.
        if ischar(fieldName)
            % varStr와 일치하는 필드를 테이블로 추가합니다.
            if isnumeric(fieldValue) || islogical(fieldValue) 
                % 숫자형 데이터 또는 셀 데이터인 경우, 단위 정보를 가져와 테이블에 추가합니다.
                matchingIndex = find(contains(targetStr, fieldName));
                if ~isempty(matchingIndex)
                    unit = unitInfo{matchingIndex};
                    if ischar(unit)
                        dataTable.(fieldName) = flattenMatrix(fieldValue);
                        dataTable.Properties.VariableUnits{fieldName} = unit;
                    else
                        warning('단위(unit) 정보가 잘못 설정되었습니다.');
                    end
                otherStruct.('sizeofVar') =size(fieldValue);
                else
              %% VarStr에 있지 않은 (기타정보)들을 별도 구조체로 저장 
                otherStruct.(fieldName)=satuMapData.(fieldName);
                end                     
            end
        else
               warning(fieldName);
        end
    end
end

