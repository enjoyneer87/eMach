function datetimeObj=mkDateTimeType(creationDate,InputForMat)
    if nargin<2
    InputForMat='dd-MM-yyyy HH:mm:ss';
    end
    creationDate = strtrim(creationDate);
    fprintf('The formatted creation date of the file is: %s\n', creationDate);
    
    % 문자열을 datetime 객체로 변환
    datetimeObj = datetime(creationDate, 'InputFormat', InputForMat);
    fprintf('The datetime object is: %s\n', datetimeObj);
end
