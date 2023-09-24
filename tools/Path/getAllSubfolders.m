function subfolders = getAllSubfolders(directory)
    % 함수 설명:
    % 주어진 디렉터리에서 모든 하위 폴더를 추출하는 함수

    % 디렉터리에서 모든 내용을 가져옵니다.
    contents = dir(directory);

    % 디렉터리 내용 중 폴더만 필터링합니다.
    subfolderIndex = [contents(:).isdir];
    subfolders = {contents(subfolderIndex).name};

    % '.'(현재 폴더)와 '..'(상위 폴더)를 제외합니다.
    subfolders = subfolders(~ismember(subfolders, {'.', '..'}));
    
    % 각 하위 폴더의 전체 경로를 생성합니다.
    subfolders = cellfun(@(x) fullfile(directory, x), subfolders, 'UniformOutput', false);
end
