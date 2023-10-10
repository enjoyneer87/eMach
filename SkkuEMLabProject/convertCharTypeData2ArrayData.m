function arrayData = convertCharTypeData2ArrayData(charTypeData)
    % originalFieldName: 변수 이름 (원본)
    % charTypeData가 문자열이면서 ':'이 포함되었는지 확인
    if ischar(charTypeData) && contains(charTypeData, ':')          % char Type Data이면서 ':'로 구분된 ArrayData인지 확인
        ArrayIndex = count(charTypeData, ':') + 1;                  % ':' 의 개수 즉 ArrayData의 value 수
        arrayData = zeros(ArrayIndex,1);  
        dataCellArray = strsplit(charTypeData, ':');                % ':'를 기준으로 문자열을 분할하여 셀 배열로 변환            
        for i = 1:ArrayIndex                                        % 배열 인덱스 개수만큼 반복하여 데이터 가져오기   
            arrayData(i) = str2double(dataCellArray{i});   % 셀 배열의 각 요소를 숫자로 변환하여 변수에 저장
        end
    elseif ischar(charTypeData) && count(charTypeData, ':')==0          
        arrayData = str2double(charTypeData);                % 가져온 데이터를 숫자로 변환하여 변수에 저장
    elseif isa(charTypeData, 'int32')           
        arrayData = double(charTypeData);
    elseif iscell(charTypeData)
        arrayCell=charTypeData{:};
        arrayData=convertCharTypeData2ArrayData(arrayCell);
    else
        arrayData=charTypeData;
    end
end



