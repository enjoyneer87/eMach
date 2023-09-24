function subfolderNames = extractSubfolderNames(folderPath)
    % folderPath: 하위 폴더 이름을 추출할 상위 폴더의 경로

    % 주어진 폴더 경로에서 모든 항목의 정보를 얻습니다.
    dirInfo = dir(folderPath);

    % 폴더 정보에서 폴더의 이름을 추출합니다.
    isSubfolder = [dirInfo(:).isdir];  % 폴더 여부를 나타내는 논리 배열
    subfolderNames = {dirInfo(isSubfolder).name}; % 폴더 이름 추출

    % 상위 폴더 ('.'와 '..') 제거
    subfolderNames = subfolderNames(~ismember(subfolderNames, {'.', '..'}));
end
