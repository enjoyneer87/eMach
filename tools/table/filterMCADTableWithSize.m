function matchingRows2Table = filterMCADTableWithSize(MCADTable, height2Find, width2Find)
    if nargin < 2
        error('최소한 MCADTable과 height2Find를 입력해야 합니다.');
    end
    
    if nargin < 3
        % 높이만 주어진 경우
        col1 = MCADTable.CurrentValue;
        matchingIndices = find(cellfun(@(x) size(x, 1) == height2Find, col1));
        matchingRows2Table = MCADTable(matchingIndices, :);
    else
        col1 = MCADTable.CurrentValue;
        matchingIndices = find(cellfun(@(x) size(x, 1) == height2Find && size(x, 2) == width2Find, col1));
        matchingRows2Table = MCADTable(matchingIndices, :);
    end
end
