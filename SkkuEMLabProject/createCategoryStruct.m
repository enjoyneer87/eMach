function ActiveXParametersStruct = createCategoryStruct(ActiveXParameters)
    % ActiveXParameters.Category 열의 고유한 카테고리 값들을 가져옵니다
    uniqueCategories = categories(ActiveXParameters.Category);
    
    % 구조체 초기화
    ActiveXParametersStruct = struct();
    
    % 각 카테고리 값에 대한 구조체 필드 생성
    for i = 1:length(uniqueCategories)
        category = uniqueCategories{i};
        
        % 해당 카테고리 값에 대한 테이블 생성
        categoryTable = ActiveXParameters(ActiveXParameters.Category == category, :);
        
        % 구조체 필드 이름으로 카테고리 이름을 사용하고, 해당 카테고리 값의 테이블을 저장
        ActiveXParametersStruct.(category) = categoryTable;
    end
end
