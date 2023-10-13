function varNamesCell=getVarNameFromMatData(EffimapData,DataType)

    fieldNames=fieldnames(EffimapData);
    fieldClass={};
    for i = 1:length(fieldNames)
        fieldName = fieldNames{i};
        fieldClass{i} = class(EffimapData.(fieldName));  
    end
     % 높이가 1인 변수명만 저장할 셀 배열 초기화
     varNamesCell = {};
    
    % 높이가 1인 변수명 구하기
    for i = 1:numel(fieldClass)
       if strcmp(fieldClass{i},DataType) 
            varNamesCell{end+1} = fieldNames{i};
        end
    end
    varNamesCell=varNamesCell';


end