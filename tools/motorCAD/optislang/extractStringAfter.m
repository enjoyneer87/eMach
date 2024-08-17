function extractedStrings = extractStringAfter(matchedWithCSVFileArrayVariable,delimistring)
% ',' 뒤의 문자열 추출
extractedStrings = {};
for i = 1:numel(matchedWithCSVFileArrayVariable)
    comma_index = strfind(matchedWithCSVFileArrayVariable{i}, delimistring);
    if ~isempty(comma_index)
        extractedStrings{end+1} = matchedWithCSVFileArrayVariable{i}(comma_index+1:end);
    end
end
end