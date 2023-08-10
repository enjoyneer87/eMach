function firstStruct=create2layerStructFromCell(cellObj)
    % 구조체 생성
    firstStruct = struct();
    
    for i = 1:numel(cellObj)
        line = cellObj{i};
        parts = strsplit(line, '.');
        
        if numel(parts) == 2
            fieldNameAndValue = strsplit(parts{2}, '=');
            fieldName = fieldNameAndValue{1};
            fieldValue = [];  % 초기값은 빈 배열
            
            % = 뒤의 값을 추출하여 저장
            if numel(fieldNameAndValue) > 1
                fieldValue = fieldNameAndValue{2};
            end
            
            % 필드 이름에 _를 제외한 특수 기호나 []가 포함될 경우 대체
            if any(fieldName ~= '_' & (fieldName < 'a' | fieldName > 'z') & (fieldName < 'A' | fieldName > 'Z') & (fieldName < '0' | fieldName > '9'))
                fieldName = regexprep(fieldName, '[^a-zA-Z0-9_]', '__');
            end
            
            % 2단계 구조체 이름
            secondLayerStructName = parts{1};
            % 중첩된 필드 이름에 _를 제외한 특수 기호나 []가 포함될 경우 대체
            if any(secondLayerStructName ~= '_' & (secondLayerStructName < 'a' | secondLayerStructName > 'z') & (secondLayerStructName < 'A' | secondLayerStructName > 'Z') & (secondLayerStructName < '0' | secondLayerStructName > '9'))
                secondLayerStructName = regexprep(secondLayerStructName, '[^a-zA-Z0-9_]', '__');
            end    
            if isvarname(secondLayerStructName)
            % 구조체에 필드 추가
                if isfield(firstStruct, secondLayerStructName)
                    if isvarname(fieldName)
                    firstStruct.(secondLayerStructName).(fieldName) = fieldValue;
                    end
                else
                    if isvarname(fieldName)
                    firstStruct.(secondLayerStructName) = struct();
                    firstStruct.(secondLayerStructName).(fieldName) = fieldValue;
                    end
                end
            end
         end
    end
    
    % 구조체 반환
    save('output_struct.mat', 'firstStruct');
    disp('구조체 생성이 완료되었습니다.');
end
