function folderNames = getSubPathStructList(parentPath)
    % parentPath의 하위 디렉토리 정보를 구조체로 가져옴
    dirStruct = dir(parentPath);
    names = {dirStruct.name};  % 구조체의 name 필드 추출
    
    % .과 ..을 제거
    indicesToRemove = strcmp(names, '.') | strcmp(names, '..');
    dirStruct(indicesToRemove) = [];  % 해당 인덱스의 항목 삭제
    
    % 폴더만 필터링
    isFolder = [dirStruct.isdir];  % isdir 속성을 사용하여 폴더 여부 확인
    folderStruct = dirStruct(isFolder);  % 폴더만 포함하는 구조체 배열 생성
    
    % 폴더 이름만을 추출
    folderNames = {folderStruct.name}';  % 폴더 구조체에서 이름만 추출

    % disp(folderNames);  % 최종 추출된 폴더 이름 출력
end
