function charTypeData = convertArrayData2CharTypeData(arrayData)
    if isnumeric(arrayData)
        if isscalar(arrayData)
            charTypeData = num2str(arrayData);
        else
            charArray = arrayfun(@(x) num2str(x), arrayData, 'UniformOutput', false);
            charTypeData = strjoin(charArray, ':');
        end
    elseif ischar(arrayData)
        charTypeData = arrayData;
    else
        error('Unsupported data type');
    end
end
