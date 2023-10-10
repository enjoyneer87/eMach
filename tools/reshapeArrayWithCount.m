function reshapedMatrix = reshapeArrayWithCount(inputArray)
    % Find unique values and their indices
    uniqueValues = unique(inputArray);
    indices = find(diff(inputArray) ~= 0);
   
    % Calculate counts for each unique value
    counts = [indices(1); diff(indices)];
    
    % Create reshaped array
    reshapedMatrix = reshape(inputArray,  counts(1),length(inputArray)/counts(1));
end
