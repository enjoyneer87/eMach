function isInt = isInteger(value)
    isInt = isnumeric(value) && value == floor(value);
end

