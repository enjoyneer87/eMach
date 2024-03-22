function matchingIndices = findMatchingIndex(list2search, str,findType)
    if nargin>2
        checkType=checkfindType(findType);
    else
        checkType=0;
    end
    % 주어진 조건에 따라 인덱스를 찾는 함수
    matchingIndices = [];
    % if isstruct({list2search})
    %     matchingIndices = strcmp({list2search}, str);
    if ~iscell(list2search)
        list2search=cellstr(list2search);
    end

    %% cellstr

    if iscell(list2search) || iscategorical(list2search)
        for i = 1:numel(list2search)
            if iscell(list2search)
                if checkType==1  
                    if strcmp(list2search{i}, str)
                        matchingIndices = [matchingIndices i]; % 일치하는 것이면 인덱스 저장
                    end
                elseif checkType==0 
                    if contains(list2search{i}, str,'IgnoreCase',true)
                    matchingIndices = [matchingIndices i]; % 일치하는 것이면 인덱스 저장
                    end
                end
            elseif iscategorical(list2search) && any(contains(char(list2search(i)), str,'IgnoreCase',true))
                matchingIndices = [matchingIndices i]; % 일치하는 것이면 인덱스 저장
            end
        end
    end
end

% 
% function matchingIndices = findMatchingIndex(list2search, str)
%     % 주어진 조건에 따라 인덱스를 찾는 함수
% 
%     % 비셀 배열을 셀 배열로 변환
%     if ~iscell(list2search)
%         list2search = cellstr(list2search);
%     end
% 
%     % 범주형 배열을 문자열 셀 배열로 변환
%     if iscategorical(list2search)
%         list2search = cellstr(list2search);
%     end
% 
%     % 일치하는 요소의 인덱스 찾기
%     matchingIndices = find(contains(list2search, str, 'IgnoreCase', true));
% end
