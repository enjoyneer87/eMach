function filteredTable = extractByCategory(AssemItemTable, categoryValue)
    % AssemItemTable의 Type 변수를 category형으로 변환
    
    % categoryValue에 해당하는 행들을 추출
    filteredTable = AssemItemTable(AssemItemTable.Type == categoryValue, :);
end
