function designNumber = extractDesignNumber(parentPath)
    % 파일명에서 Designxxx 번호 추출
    expression = '(Design\d{3})';
    matches = regexp(parentPath, expression, 'match');
    if isempty(matches)
        designNumber = '';
    else
        designNumber = matches{1};
    end
end

