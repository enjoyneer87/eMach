function myStruct=createStructFromText(inputFilePath)
    
    % 파일 읽기
    fileID = fopen(inputFilePath, 'r');
    data = textscan(fileID, '%s', 'Delimiter', '\n');
    fclose(fileID);
    
    % 구조체 생성 및 필드 이름 변환을 저장하는 구조체 초기화
    myStruct = struct();
    fieldReplacement = struct();
    
    for i = 1:numel(data{1})
        line = data{1}{i};
        parts = strsplit(line, '.');
        
        if numel(parts) == 2
            fieldName = parts{2};
            fieldValue = parts{2};  % 기본값은 fieldName
            
            % Field 이름에 특수 기호나 []가 포함될 경우 _로 대체
            if ~isvarname(fieldName)
                newFieldName = regexprep(fieldName, '[^a-zA-Z0-9]', '_');
                fieldValue = newFieldName;
                fieldReplacement.(newFieldName) = fieldName;
                fieldName = newFieldName;
            end
            
            % = 뒤의 값을 추출하여 저장
            valueIndex = strfind(parts{2}, '=');
            if ~isempty(valueIndex)
                fieldValue = parts{2}(valueIndex+1:end);
            end
            
            % 구조체에 필드 추가
            myStruct.(fieldName) = fieldValue;
        end
    end
    
    % 필드 이름 대체 사항 저장
    save('field_replacement.mat', 'fieldReplacement');
    
    % 구조체 반환
    save('output_struct.mat', 'myStruct');
    disp('구조체 생성이 완료되었습니다.');
end
