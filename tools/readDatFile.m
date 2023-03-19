function dataTable = readDatFile(filepath, NumVariables, headerLines)

    % 파일 확장자 추출
    [~,~,ext] = fileparts(filepath);

    if strcmp(ext,'.dat')
        % DAT 파일인 경우
        % 파일 옵션 지정
        fileOpts = delimitedTextImportOptions("NumVariables", NumVariables, "Encoding", "UTF-8");
        fileOpts.DataLines = [headerLines+1, inf];
        fileOpts.VariableNamesLine = headerLines;
        fileOpts.Delimiter = ",";
        fileOpts.VariableTypes = repmat({'double'}, 1, NumVariables);
        fileOpts.ExtraColumnsRule = "ignore";
        fileOpts.EmptyLineRule = "read";

        % 데이터 가져오기
        dataTable = readtable(filepath, fileOpts);

    else
        error('Unsupported file extension. Only .dat files are supported.')
    end

end