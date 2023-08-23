function EMMapStruct = getEMMap(tempCasepath, EMFilesinFolder)
    
    % 첫번째 mat 파일을 data구조체로 불러오기 
    dataFields = {};  %  필드 목록 
    EMFileIndex = 1;
    EMFileName = EMFilesinFolder{1, EMFileIndex};  
    EMFilePath = fullfile(tempCasepath, EMFileName);
    data = load(EMFilePath);

    % EMMapStruct 구조체 (파일개수만큼 행) 미리 선언하기   
    EMMapStruct = struct(); % 빈 구조체로 초기화
    if isempty(dataFields)
        dataFields = fields(data);
        % EMFileName 필드 추가
        dataFields = [dataFields; 'EMFileName'];
        % EMFileName 필드 초기화
        EMMapStruct.(dataFields{end}) = '';
        % 데이터 파일의 필드 목록 업데이트
        for i = 1:length(dataFields)-1
            EMMapStruct.(dataFields{i}) = [];            
        end
    end
  
    % 미리 할당된 EMmap구조체에 정보 get
    for EMFileIndex = 1:length(EMFilesinFolder)    
        EMFileName = EMFilesinFolder{1, EMFileIndex};
        EMFilePath = fullfile(tempCasepath, EMFileName);
        EMMapStruct(EMFileIndex).(dataFields{end}) = EMFileName;
        data = load(EMFilePath);
        for i = 1:length(dataFields)-1
            EMMapStruct(EMFileIndex).(dataFields{i}) = data.(dataFields{i});
        end
    end 

end


% function EMMapStruct = getEMMap(tempCasepath, EMFilesinFolder)
%     
%     % 첫번째 mat 파일을 data구조체로 불러오기 
%     dataFields = {};  %  필드 목록 
%     EMFileIndex=1;
%     EMFileName=EMFilesinFolder{1,EMFileIndex};  
%     EMFilePath=fullfile(tempCasepath, EMFileName);
%     data = load(EMFilePath);
% 
%     % EMMapStruct 구조체 (파일개수만큼 행) 미리 선언하기   
%     EMMapStruct = struct(); % 빈 구조체로 초기화
%     if isempty(dataFields)
%         dataFields = fields(data);
%     % 데이터 파일의 필드 목록 업데이트
%         for i = 1:length(dataFields)
%             EMMapStruct.(dataFields{i}) = [];            
%         end
%     end
%   
%     % 미리 할당된 EMmap구조체에 정보 get
%     for EMFileIndex=1:length(EMFilesinFolder)    
%         EMFileName=EMFilesinFolder{1,EMFileIndex};
%         EMFilePath=fullfile(tempCasepath, EMFileName);
%         EMMapStruct(EMFileIndex)=load(EMFilePath);
%     end 
% 
% end

