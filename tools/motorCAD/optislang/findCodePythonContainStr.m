function [matched_lines, matched_lines_without_comment] = findCodePythonContainStr(python_file_path, search_string)
% Python 코드 파일 읽어들이기
file_content = fileread(python_file_path);

% 특정 문자열이 사용된 라인 검색
lines = strsplit(file_content, '\n');
matched_lines = {};
for i = 1:numel(lines)
    % 라인의 앞뒤 공백 제거
    line = strtrim(lines{i});
    
    % 맨 첫 글자가 '#'이 아닌 라인만 추출
    if ~startsWith(line, '#') && contains(line, search_string)
        matched_lines{end+1} = line;
    end
end

% 문자열 앞부분에 '#'이 있는 부분만 추출
matched_lines_without_comment = {};
for i = 1:numel(matched_lines)
    line = matched_lines{i};
    idx = strfind(line, '#');
    if ~isempty(idx)
        line = line(1:idx-1);
    end
    matched_lines_without_comment{end+1} = line;
    matched_lines_without_comment=strtrim(matched_lines_without_comment);
end

% 결과 출력
if isempty(matched_lines)
    disp('해당 문자열이 사용된 라인이 없습니다.');
else
    disp('특정 문자열이 사용된 라인:');
    for i = 1:numel(matched_lines)
        disp(matched_lines{i});
    end
end
end