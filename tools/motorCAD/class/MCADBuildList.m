classdef MCADBuildList
    properties
    MotFilePath
    LabBuildDate
    MotFileDate
    IsBuildFromDate  % LabBuildDate가 MotFileDate보다 이후인지 여부
    end

    methods
        function obj = MCADBuildList(input2GetData)
        % 병렬 풀 설정
        if isempty(gcp('nocreate'))
            parpool;  % 기본 설정으로 병렬 풀 시작
        end
%% MOTFilePath
        if isstring(input2GetData)    
            MotFileList = findMOTFiles(input2GetData)';
            MotFileList = removeAutoSaveFiles(MotFileList)';
            MotFileList = removeBackupFiles(MotFileList);
            MotFileList = MotFileList(~contains(MotFileList, 'Scale'));
            MotFileList = MotFileList(~contains(MotFileList, 'SL'));
            MotFileList = MotFileList(~contains(MotFileList, 'MCAD'));
        elseif istable(input2GetData)
            if isvarofTable(input2GetData,'ParentPath')
            MotFileDirList=fullfile(input2GetData.ParentPath,input2GetData.FileDir);
            MotFileList   =fullfile(MotFileDirList,input2GetData.FileName);
            elseif isvarofTable(input2GetData,'MotFilePath')
            MotFileList=input2GetData.MotFilePath;
            end
        elseif iscell(input2GetData)
            MotFileList=input2GetData;
        end
        %% Class       
        % MotFileList = MotFileList';  
        obj.MotFilePath=MotFileList;
        %% Build MessageLog
        MessageDate = cell(1, numel(MotFileList));  % 초기화
        MotFileDate = cell(1, numel(MotFileList));  % 초기화
    
        parfor MotFileIndex = 1:numel(MotFileList)
            [parentDir,MotFileName,~]=fileparts(MotFileList{MotFileIndex})
            MessageLogsList = findTXTFiles(fullfile(parentDir,MotFileName))';
            MessageLogsList = MessageLogsList(contains(MessageLogsList,'messageLog'))
            if ~isempty(MessageLogsList)
                % get Latest MessageLog
                lastwriteDateList = getLastWriteDateList(MessageLogsList);
                lastwriteDateList={lastwriteDateList(:).LastDate};
                % latestIndex       = findMostRecentIndex(lastwriteDateList);              
                latestIndex=1
                MessageLogData    = getTXTdataScan(MessageLogsList{latestIndex});
                MessageLog        = checkMCADMessageLog4LabBuild(MessageLogData);              
                if ~isempty(MessageLog)
                    MessageDate{MotFileIndex} = MessageLog;
                else                   
                    MessageDate(MotFileIndex) =  input2GetData.SatDate(MotFileIndex) ;  % 공백 문자열로 초기화
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
                        labDate = datetime(obj.LabBuildDate{1}, 'InputFormat', 'dd-MM-yy HH:mm', 'Locale', 'en_US');
                        motDate = datetime(obj.MotFileDate{i}, 'InputFormat', 'dd/MM/yyyy HH:mm:ss', 'Locale', 'en_US');
                        if labDate > motDate
                            result(i) = 1; % LabBuildDate가 MotFileDate보다 이후
                        else
                            result(i) = 3; % LabBuildDate가 MotFileDate보다 이전
                        end
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