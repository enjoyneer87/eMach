function myStruct=convertMCADActiveXTable2MCADVarStruct(ActiveXTable)
    % categoryName을 구조체 이름으로 사용하여 구조체 필드에 접근합니다.
    structFieldName = ActiveXTable.AutomationName;    
    % categoryName을 사용하여 구조체를 생성하고 필드에 값을 할당합니다.
    myStruct = struct();
    for fieldIndex = 1:length(structFieldName)
        myStruct.(structFieldName{fieldIndex}) = ActiveXTable.CurrentValue{fieldIndex};
    end
end

