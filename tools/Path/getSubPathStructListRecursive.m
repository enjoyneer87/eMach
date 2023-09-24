function myStruct = getSubPathStructListRecursive(parentPath)
    % .과 ..이 포함된 행 삭제
    myStruct = dir(parentPath);
    names = {myStruct.name};  % 구조체의 name 필드 추출
    indicesToRemove = strcmp(names, '.') | strcmp(names, '..');  % .과 ..에 해당하는 인덱스 찾기
    myStruct(indicesToRemove) = [];  % 해당 인덱스의 행 삭제

    % 현재 디렉터리(parentPath)의 하위 폴더 목록 추출
    subfolders = myStruct([myStruct.isdir]);
    
    % 하위 폴더에 대해 재귀적으로 동작
    for i = 1:length(subfolders)
        subfolderName = subfolders(i).name;
        if ~strcmp(subfolderName, '.') && ~strcmp(subfolderName, '..')
            subfolderPath = fullfile(parentPath, subfolderName);
            subfolderContents = getSubPathStructListRecursive(subfolderPath);
            % 하위 폴더의 목록을 현재 구조체에 추가
            myStruct(i).subfolders = subfolderContents;
        end
    end
end
