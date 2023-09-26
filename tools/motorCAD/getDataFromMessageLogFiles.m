function CalcCheckStruct = getDataFromMessageLogFiles(MessageLogFiles)
    % 파일 읽기
    % MessageLogFiles = findMessageLogFiles(simulPath)';
    AutoSaveChecker = ~contains(MessageLogFiles, 'AutoSave');
    NotAutoFileSaveLog = MessageLogFiles(AutoSaveChecker);

    DesignNumberList = fileparts(fileparts(NotAutoFileSaveLog));
    DesignNumberList = unique(DesignNumberList);

    CalcCheckStruct = struct(); % 빈 구조체 생성

    for DesignNumberIndex = 1:length(DesignNumberList)
        [DesignNumberPath, DesignNumber, ~] = fileparts(DesignNumberList{DesignNumberIndex});
        MessageLogFilesPerDesign = findMessageLogFiles(DesignNumberPath)';
        AutoSaveCheckerPerDesign = ~contains(MessageLogFilesPerDesign, 'AutoSave');
        NotAutoFileSaveLogPerDesign = MessageLogFilesPerDesign(AutoSaveCheckerPerDesign);
        
        % LoggName과 LogContents를 가지는 빈 테이블 생성
        CalcCheckStruct.(strcat('field', DesignNumber)).CalcLines = table([], {}, 'VariableNames', {'LoggName', 'LogContents'});

        for MessageLogPerDesignIndex = 1:length(NotAutoFileSaveLogPerDesign)
            lines = readlines(NotAutoFileSaveLogPerDesign{MessageLogPerDesignIndex});
            [~, messageName, ~] = fileparts(NotAutoFileSaveLogPerDesign);
            CalcChecker = contains(lines, 'completed');
            CalcLines = lines(CalcChecker);

            % 테이블에 데이터 추가
            for StringLineIndex=1:length(CalcLines)
            newRow= table(messageName(MessageLogPerDesignIndex), {CalcLines{StringLineIndex}}, 'VariableNames', {'LoggName', 'LogContents'});
            CalcCheckStruct.(strcat('field', DesignNumber)).CalcLines = [CalcCheckStruct.(strcat('field', DesignNumber)).CalcLines; newRow];
            end

            % newTable = table(messageName(MessageLogPerDesignIndex), strjoin(CalcLines, '\n'), 'VariableNames', {'LoggName', 'LogContents'});
            % CalcCheckStruct.(strcat('field', DesignNumber)).CalcLines = [CalcCheckStruct.(strcat('field', DesignNumber)).CalcLines; newTable];
         end
    end
end
