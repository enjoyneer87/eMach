function MessageDate=checkMCADMessageLog4LabBuild(MessageLogData)


    %% 텍스트 검토 알고리즘
    for i = 1:numel(MessageLogData{1})  
        %% Get Lab Build Info (SLFEA or DOE)
        TotalCalcTime       =find(contains(MessageLogData{1},'SetVariable LabModel_Saturation_Date')); 
        if ~isempty(TotalCalcTime)
        LastTotalCalcIndex  =TotalCalcTime(end);   
        LastTotalCalcString =MessageLogData{1}{LastTotalCalcIndex}; 
        splitedString=strsplit(LastTotalCalcString,'= ');
            if length(splitedString)>1
            part1=splitedString{2};
            part1=strrep(part1,'-','/');
            end
        % %% ':' 문자의 모든 위치 찾기
        % colonIndices = strfind(LastTotalCalcString, ':');
        % 
        %     % 세 번째 ':'이 있는지 확인하고 문자열을 분할
        %     if length(colonIndices) >= 3
        %         % 세 번째 ':'의 인덱스
        %         thirdColonIndex = colonIndices(3);    
        %         % 세 번째 ':' 기준으로 문자열 분할
        %         part1 = LastTotalCalcString(1:thirdColonIndex-1);
        %         part2 = LastTotalCalcString(thirdColonIndex+1:end);
        %     end
        end
    end
    
    %% Date
    if exist('part1',"var")&&~isempty(part1)
    MessageDate = datetime(part1, 'InputFormat', 'dd/MM/yy HH:mm'); 
    % MessageDate = datetime(part1, 'InputFormat', 'dd/MM/yyyy a h:mm:ss', 'Locale', 'ko_KR');
    % MessageLog.MessageDate              =MessageDate;
    %% MessageLog Struct
    % MessageLog.CheckLabComplete         =CheckLabComplete;
    % MessageLog.CheckCANCELCALC_MOTORLAB =CheckCANCELCALC_MOTORLAB;
    else
    MessageDate='';
    end

end

