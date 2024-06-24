function splitMotDataStruct = splitDataByMCADcategory(motcelldata)
    % 특정 조건에 맞는 MCADcategory 추출
    emptyCells = cellfun(@isempty, motcelldata);
    motcelldata = motcelldata(~emptyCells);
    keywordIndices=find(~contains(motcelldata, '='));
    % 분리된 셀 배열 초기화
    splitMotDataStruct=struct();
    % MCADcategory 요소들 기준으로 data를 분리
    MCADcategoryList=motcelldata(keywordIndices);
    MCADcategoryList = removeAllSpecialCharacters(MCADcategoryList);
    MCADcategoryList=replaceSpacesWithUnderscores(MCADcategoryList);    
    %%  MCAD 구조체로 가져오기
    for i = 1:numel(keywordIndices)         
        fieldName = prependMatIfStartsWithNumber(MCADcategoryList{i});
        if i~=numel(keywordIndices)      
        splitMotDataStruct.(fieldName) = motcelldata(keywordIndices(i)+1:keywordIndices(i+1)-1);
        else
        splitMotDataStruct.(fieldName) = motcelldata(keywordIndices(i)+1:end);  
        end
    end
end

