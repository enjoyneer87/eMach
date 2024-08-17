function categoryStructTable=sortAssemItemTableByType(geomApp,AssembleName)

AssemTable = getGeomAssemItemListTable(geomApp);
AssemItemObj=AssemTable.AssemItem(contains(AssemTable.AssemItemName,AssembleName));
AssemItemTable = getGeomObjItemListTable(AssemItemObj);
AssemItemTable.Type = categorical(AssemItemTable.Type);
categoryList  = categories(AssemItemTable.Type);
% categoryValue = categoryList{contains(categoryList,'mirror','IgnoreCase',true)};

categoryStructTable=struct();

for i = 1:length(categoryList)
    categoryValue = categoryList{i};
    % 특정 카테고리에 해당하는 행들을 추출
    filteredTable = extractByCategory(AssemItemTable, categoryValue);

    % filteredTable = AssemItemTable(AssemItemTable.Type == categoryValue, :);
    % 구조체에 테이블 저장
    categoryStructTable.(categoryValue) = filteredTable;
end

end