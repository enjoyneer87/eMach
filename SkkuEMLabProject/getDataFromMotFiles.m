function modifiedData=getDataFromMotFiles(MotFilePath)
    % 파일 읽기
    fileID = fopen(MotFilePath, 'r');
    data = textscan(fileID, '%s', 'Delimiter', '\n');
    fclose(fileID);
    
    % 수정된 데이터와 [] 안의 텍스트, [] 안의 텍스트 리스트를 저장할 변수 초기화
    modifiedData = {};
    textInsideBrackets = '';
    textInsideBracketsList = {};
    
    for i = 1:numel(data{1})
        line = data{1}{i};
        
        % []로 시작하여 []로 끝나는 행인 경우
        if ~isempty(line) && line(1) == '[' && line(end) == ']'
            textInsideBrackets = line(2:end-1); % [] 안의 텍스트 추출
            textInsideBracketsList{end+1} = textInsideBrackets; % [] 안의 텍스트 리스트에 저장
        elseif ~isempty(line)
            % [] 안의 텍스트가 있을 때만 수정된 데이터 생성
            if ~isempty(textInsideBrackets)
                modifiedData{end+1, 1} = [textInsideBrackets, '.', line];
            else
                modifiedData{end+1, 1} = line;
            end
        end
    end
end