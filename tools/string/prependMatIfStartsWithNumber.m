function modifiedStr = prependMatIfStartsWithNumber(inputStr)
    % Check if the input string starts with a digit
    if ~isempty(inputStr) && isstrprop(inputStr(1), 'digit')
        % Prepend 'mat' to the input string
        modifiedStr = ['mat', inputStr];
    else
        % Return the input string as is
        modifiedStr = inputStr;
    end
end
