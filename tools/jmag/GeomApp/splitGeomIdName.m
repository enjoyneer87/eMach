function splitedIdNameCell=splitGeomIdName(IdentifierName)

    % 이 함수는 입력된 문자열을 '+', ')', '('를 기준으로 나눕니다.

    % 나누는 기준이 되는 문자들을 정의합니다.
    delimiters = {'+', ')', '('};

    % 문자열을 나눕니다.
    % if iscell(IdentifierName)
    % splitedIdNameCell = strsplit(IdentifierName, delimiters);
    % else 
    splitedIdNameCell = strsplit(IdentifierName, delimiters);
    % end
end