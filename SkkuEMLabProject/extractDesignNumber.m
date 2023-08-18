function designNumber = extractDesignNumber(parentPath)
    % 파일명에서 Designxxxx 번호 추출
    expression = '(Design\d{4})';
    matches = regexp(parentPath, expression, 'match');
    if isempty(matches)
        designNumber = '';
    else
        designNumber = matches{1};
    end
end

