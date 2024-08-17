function variable_names=findVariableNameMotorCADfcn(matched_lines,search_string)
% 찾을 문자열
% search_string = 'SetVariable("';

% SetVariable 다음에 있는 문자열 추출
variable_names = {};
for i = 1:numel(matched_lines)
    if contains(matched_lines{i}, search_string)
        index1 = strfind(matched_lines{i}, search_string);
        index2 = strfind(matched_lines{i}, ',');
        variable_name = strtrim(matched_lines{i}(index1+numel(search_string):index2-1));
        variable_name = strrep(variable_name, '''', ''); % 작은따옴표(') 제거
        variable_name = strrep(variable_name, '"', ''); % 쌍따옴표(") 제거
        variable_names{i}=variable_name;
    end
end

% 결과 출력
if isempty(variable_names)
    disp('해당 문자열이 사용된 라인이 없습니다.');
else
    disp('SetVariable 다음에 나오는 변수 이름:');
    for i = 1:numel(variable_names)
        disp(variable_names{i});
        
    end
end
end