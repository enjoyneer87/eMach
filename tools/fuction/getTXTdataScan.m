function data=getTXTdataScan(FilePath)
    % 파일 읽기
    fileID = fopen(FilePath, 'r');
    data = textscan(fileID, '%s', 'Delimiter', '\n');
    fclose(fileID);
end