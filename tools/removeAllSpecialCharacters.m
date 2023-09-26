function cleanedString = removeAllSpecialCharacters(inputString)
    % 정규 표현식을 사용하여 특수문자를 제거
    cleanedString = regexprep(inputString, '[^a-zA-Z0-9 ]', '');
end
