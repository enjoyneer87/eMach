function out=autoVariableFindFromCell(VariableNames,strings_to_find)
%
% VariableNames 는 Cell 형태 
% VariableNames = {'text string1', 'some other string', 'string3 is here', 'no match'};
% 특정 문자열을 사전에 정의
% strings_to_find = {'o_', 'obj_', 'constr'};

%% string name
cell_array=VariableNames;

% 포함되지 않은 문자열 찾기
no_match_indices = [];
for i = 1:numel(cell_array)
    is_match = false;
    for j = 1:numel(strings_to_find)
        if contains(cell_array{i}, strings_to_find{j})
            is_match = true;
            break;
        end
    end
    if ~is_match
        no_match_indices(end+1) = i;
    end
end

% 결과 출력
if isempty(no_match_indices)
    disp('모든 셀이 검색 문자열을 포함합니다.');
    out=[];
else
    disp('검색 문자열 중 하나도 포함되지 않은 셀:');
    disp(cell_array(no_match_indices));
    out=cell_array(no_match_indices);
end

end