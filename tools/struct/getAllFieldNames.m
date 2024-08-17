function fieldNames = getAllFieldNames(structVar)
    fieldNames = {}; % 필드 이름들을 저장할 셀 배열 초기화
    fieldNames = extractFieldNames(structVar, '', fieldNames);
end

function fieldNames = extractFieldNames(s, prefix, fieldNames)
    % 주어진 구조체의 모든 필드 이름을 추출하여 fieldNames에 추가
    
    if isstruct(s)
        fields = fieldnames(s); % 현재 구조체의 필드 이름 추출
        for i = 1:length(fields)
            field = fields{i};
            fullFieldName = [prefix '\' field]; % 전체 필드 이름 생성
            fieldNames{end+1} = fullFieldName; % 필드 이름 추가
            
            % 필드가 구조체일 경우 재귀적으로 호출
            if isstruct(s.(field))
                fieldNames = extractFieldNames(s.(field), [fullFieldName '.'], fieldNames);
            end
        end
    end
end
