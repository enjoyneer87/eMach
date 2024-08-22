function updatedName = updatePartName(Name,UpdateName,UpdateIndex)
    % 현재 이름을 슬래시('/') 기준으로 분할
    NameSplit = strsplit(Name, '/');
   
    
    % 첫 번째 요소를 'Stator'로 변경
    NameSplit{UpdateIndex} = UpdateName;
    
    % 다시 슬래시('/')를 기준으로 합쳐서 전체 이름을 생성
    updatedName = strjoin(NameSplit, '/');
    
    % 변경된 이름을 PartTable.Name{1}에 할당
end