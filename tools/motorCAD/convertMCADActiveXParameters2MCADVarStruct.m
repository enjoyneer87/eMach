function convertMCADActiveXParameters2MCADVarStruct(categoryName)
    % categoryName을 구조체 이름으로 사용하여 구조체 필드에 접근합니다.
    ActiveXParametersStruct=loadMCadActiveXParameter();
    ActiveXParametersStruct=ActiveXParametersStruct.ActiveXParametersStruct;
    structFieldName = ActiveXParametersStruct.(categoryName).AutomationName;
    
    % categoryName을 사용하여 구조체를 생성하고 필드에 값을 할당합니다.
    myStruct = struct();
    for fieldIndex = 1:length(structFieldName)
        myStruct.(structFieldName{fieldIndex}) = [];
    end
    
    % categoryName을 구조체의 이름으로 사용하여 구조체를 생성합니다.
    eval([categoryName ' = myStruct;']);
    
    % categoryName을 반환합니다.
end

