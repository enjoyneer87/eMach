function result = isEmptyCheck(x)
    % isEmptyCheck - 다양한 데이터 유형에 대해 값이 비어있는지 확인합니다.

    if isnumeric(x) || islogical(x)
        % 숫자형 또는 논리형 데이터의 경우
        result = isnan(x);
    elseif iscell(x)
        % 셀 배열의 경우
        result = cellfun(@(c) isempty(c) || (ischar(c) && strcmp(c, '')) || (isnumeric(c) && isnan(c)), x);
    elseif ischar(x) || isstring(x)
        % 문자형 또는 문자열형 데이터의 경우
        result = strcmp(x, '') | ismissing(x);
    elseif iscategorical(x)
        % 카테고리형 데이터의 경우
        result = isundefined(x);
    else
        % 기타 타입의 경우 ismissing으로 처리
        result = ismissing(x);
    end
end