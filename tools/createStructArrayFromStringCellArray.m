function structArray = createStructArrayFromStringCellArray(strCellArray)
    structArray = struct();  % 초기화된 구조체 배열

    % 반복문을 통해 strCellArray의 각 요소를 처리
    for i = 1:numel(strCellArray)
        % 문자열을 배열 데이터로 변환
        arrayData = convertCharTypeData2ArrayData(strCellArray{i});

        % 구조체에 데이터 추가
        fieldName = sprintf('Field%d', i);  % 필드 이름 생성
        structArray(i).FieldName = fieldName;
        structArray(i).ArrayData = arrayData;
    end
end
