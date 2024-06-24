classdef MCADBuildList
    properties
    MotFilePath
    LabBuildDate
    MotFileDate
    IsBuildFromDate  % LabBuildDate가 MotFileDate보다 이후인지 여부
    end

    methods
        function obj = MCADBuildList(DOEDIR)
        % 병렬 풀 설정
        if isempty(gcp('nocreate'))
            parpool;  % 기본 설정으로 병렬 풀 시작
        end
        %% MOTFilePath
        MotFileList = findMOTFiles(DOEDIR)';
        MotFileList = removeAutoSaveFiles(MotFileList);
        MotFileList = removeBackupFiles(MotFileList);
        % MotFileList = MotFileList';  
        obj.MotFilePath=MotFileList;
        %% Build MessageLog
        MessageDate = cell(1, numel(MotFileList));  % 초기화
        MotFileDate = cell(1, numel(MotFileList));  % 초기화
    
        parfor MotFileIndex = 1:numel(MotFileList)
            MessageLossList = findTXTFiles(fileparts(MotFileList{MotFileIndex}))';
            if ~isempty(MessageLossList)
                MessageLogData = getTXTdataScan(MessageLossList{1});
                MessageLog = checkMCADMessageLog4LabBuild(MessageLogData);
                if ~isempty(MessageLog)
                    MessageDate{MotFileIndex} = MessageLog;
                else
                    MessageDate{MotFileIndex} = '';  % 공백 문자열로 초기화
                end
            else
                MessageDate{MotFileIndex} = '';  % 파일 목록이 비어있을 경우 공백 문자열
            end
            MotFileDate{MotFileIndex} = getMOTCreateDate(MotFileList{MotFileIndex});
        end
    
        % 할당
        obj.LabBuildDate = MessageDate';
        obj.MotFileDate = MotFileDate';
        % 날짜 비교 메소드 호출
        obj.IsBuildFromDate = obj.checkDates();
        end
        
         function result = checkDates(obj)
            % LabBuildDate가 MotFileDate보다 이후인지 확인
            result = zeros(size(obj.LabBuildDate)); % 기본값을 0으로 초기화
            for i = 1:length(obj.LabBuildDate)
                if isempty(obj.LabBuildDate{i})
                    result(i) = 0; % LabBuildDate가 비어있음
                elseif ~isempty(obj.MotFileDate{i})
                    try
                        labDate = datetime(obj.LabBuildDate{i}, 'InputFormat', 'dd/MM/yyyy HH:mm:ss', 'Locale', 'en_US');
                        motDate = datetime(obj.MotFileDate{i}, 'InputFormat', 'dd/MM/yyyy HH:mm:ss', 'Locale', 'en_US');
                        if labDate > motDate
                            result(i) = 1; % LabBuildDate가 MotFileDate보다 이후
                        else
                            result(i) = 3; % LabBuildDate가 MotFileDate보다 이전
                        end
                    catch
                        result(i) = 0; % 날짜 변환에 실패할 경우 0으로 처리
                    end
                else
                    result(i) = 0; % MotFileDate가 비어있음
                end
            end
        end


        function t = toTable(obj)
            % 객체의 속성을 테이블로 변환
            % 각 속성이 셀 배열 형태로 되어 있다고 가정
            variableNames = {'MotFilePath', 'LabBuildDate', 'MotFileDate','IsBuildFromDate'};  % 테이블 변수 이름
            
            % cell2table를 사용하여 셀 배열을 테이블로 변환
            MotFilePathT = cell2table(obj.MotFilePath, 'VariableNames', variableNames(1));
            LabBuildDateT = cell2table(obj.LabBuildDate, 'VariableNames', variableNames(2));
            MotFileDateT = cell2table(obj.MotFileDate, 'VariableNames', variableNames(3));
            IsBuildT = table(obj.IsBuildFromDate, 'VariableNames', variableNames(4));

            t=[MotFilePathT LabBuildDateT MotFileDateT IsBuildT];
        end

    end
end