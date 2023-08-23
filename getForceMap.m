function forceMapStruct = getForceMap(tempCasepath, forceFilesinFolder)

    dataFields = {};  %  필드 목록 
    forceFileIndex = 1;
    forceFileName = forceFilesinFolder{1, forceFileIndex};  
    forceFilePath = fullfile(tempCasepath, forceFileName);
    data = load(forceFilePath);

    % EMMapStruct 구조체 (파일개수만큼 행) 미리 선언하기   
    forceMapStruct = struct(); % 빈 구조체로 초기화
    if isempty(dataFields)
        dataFields = fields(data);
        % EMFileName 필드 추가
        dataFields = [dataFields; 'forceFileName'];
        % EMFileName 필드 초기화
        forceMapStruct.(dataFields{end}) = '';
        % 데이터 파일의 필드 목록 업데이트
        for i = 1:length(dataFields)-1
            forceMapStruct.(dataFields{i}) = [];            
        end
    end

    % 미리 할당된 EMmap구조체에 정보 get
    for forceFileIndex = 1:length(forceFilesinFolder)    
        forceFileName = forceFilesinFolder{1, forceFileIndex};
        forceFilePath = fullfile(tempCasepath, forceFileName);
        forceMapStruct(forceFileIndex).(dataFields{end}) = forceFileName;
        data = load(forceFilePath);
        for i = 1:length(dataFields)-1
            forceMapStruct(forceFileIndex).(dataFields{i}) = data.(dataFields{i});
        end
    end 
    
end