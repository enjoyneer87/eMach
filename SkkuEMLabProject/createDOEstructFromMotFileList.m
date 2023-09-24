function DOE=createDOEstructFromMotFileList(readMotFileList)
    DOE=struct();
    for i = 1:numel(readMotFileList)
       
        % MotFileList 문자열에서 Design Number 추출
        str = readMotFileList{i};
        startIndex = strfind(str, 'Design') + length('Design');
    
        if ~isempty(startIndex)
                % DesignNumber가 시작하고 끝나는 Index 찾기
            startIndex=startIndex(2);
            endIndex = strfind(str, '.mot') - 1;
            % DesignNumber의 Str
            numberStr = str(startIndex:endIndex);
            % str2Num
            DesignNumber = str2double(numberStr);
            if ~isnan(DesignNumber)
                structName = ['Design', num2str(DesignNumber)];
                DOE.(structName)=[];
            end
        end
    end
end