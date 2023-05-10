function cellArray = addIndexToDuplicateCells(cellArray)
    [~, index] = unique(cellArray, 'stable');
    duplicates = setdiff(1:numel(cellArray), index);
    for i = duplicates
        count = 1;
        while true
            if ~ismember(sprintf('%s_%d', cellArray{i}, count), cellArray)
                cellArray{i} = sprintf('%s_%d', cellArray{i}, count);
                break
            end
            count = count + 1;
        end
    end
end