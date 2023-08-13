function value = findMatchedValueinCell(dataCell, searchValue,searchCol,returncol)
  value = []; % 반환할 값을 초기화합니다. 찾지 못한 경우 빈 배열로 반환됩니다.
  for row = 1:size(dataCell, 1)
    if dataCell{row, searchCol} == searchValue
      value = dataCell{row, returncol}; % 찾은 경우, 해당 행의 3번째 열 값을 반환합니다.
      return;
    end
  end
end
