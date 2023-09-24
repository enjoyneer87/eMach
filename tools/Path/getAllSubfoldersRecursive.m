function allSubfolders = getAllSubfoldersRecursive(directory)
    % 함수 설명:
    % 주어진 디렉터리에서 모든 하위 폴더를 재귀적으로 추출하는 함수

    % 디렉터리에서 모든 내용을 가져옵니다.
    contents = dir(directory);

    % 디렉터리 내용 중 폴더만 필터링합니다.
    subfolderIndex = [contents(:).isdir];
    subfolderNames = {contents(subfolderIndex).name};

    % '.'(현재 폴더)와 '..'(상위 폴더)를 제외합니다.
    subfolderNames = subfolderNames(~ismember(subfolderNames, {'.', '..'}));

    % 각 하위 폴더의 전체 경로를 생성합니다.
    subfolderPaths = cellfun(@(x) fullfile(directory, x), subfolderNames, 'UniformOutput', false);

    % 현재 디렉터리의 하위 폴더 목록 초기화
    allSubfolders = subfolderPaths';

    % 각 하위 폴더에 대해 재귀 호출 수행
    for i = 1:length(subfolderPaths)
        subfolder = subfolderPaths{i};
        subSubfolders = getAllSubfoldersRecursive(subfolder);
        allSubfolders = [allSubfolders; subSubfolders];
    end
end
