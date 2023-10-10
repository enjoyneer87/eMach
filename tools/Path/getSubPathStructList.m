function myStruct=getSubPathStructList(parentPath)
    % .과 ..이 포함된 행 삭제
    myStruct=dir(parentPath);
    names = {myStruct.name};  % 구조체의 name 필드 추출
    indicesToRemove = strcmp(names, '.') | strcmp(names, '..');  % .과 ..에 해당하는 인덱스 찾기
    myStruct(indicesToRemove) = [];  % 해당 인덱스의 행 삭제    
    % disp(myStruct);  % .과 ..이 삭제된 구조체 출력
    
end