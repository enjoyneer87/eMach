function varNamesCell=getVariablesHeight1FromMatData(EffimapData)

    fieldNames=fieldnames(EffimapData);
     % 높이가 1인 변수명만 저장할 셀 배열 초기화
     varNamesCell = {};
    
    % 높이가 1인 변수명 구하기
    for i = 1:numel(fieldNames)
       fieldName = fieldNames{i};
       if size(EffimapData.(fieldName),1) == 1
            varNamesCell{end+1} = fieldNames{i};
        end
    end
    varNamesCell=varNamesCell';


end