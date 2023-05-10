% 검색할 폴더 경로
folder_path = 'Z:\01_Codes_Projects\git_fork_emach';

% 검색할 문자열
search_str = 'EddyCoefficientData';

% 폴더 내 파일 목록 얻기
files = dir(fullfile(folder_path, '**', '*.m'));

% 검색된 파일 목록 저장할 리스트 초기화
result_files = {};

% 파일별로 검사
for i = 1:numel(files)
    % 파일 읽어들이기
    file_path = fullfile(files(i).folder, files(i).name);
    file_contents = fileread(file_path);
    
    % 파일 내 검색 문자열 포함 여부 검사
    if contains(file_contents, search_str, 'IgnoreCase', true)
        result_files{end+1} = file_path;
    end
end

% 검색 결과 출력
if ~isempty(result_files)
    fprintf('검색 결과:\n');
    for i = 1:numel(result_files)
        fprintf('%s\n', result_files{i});
    end
else
    fprintf('검색 실패: 검색된 파일이 없습니다.\n');
end