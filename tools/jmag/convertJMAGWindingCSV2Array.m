function ncoil = convertJMAGWindingCSV2Array(fname)
    % fname: CSV 파일 경로

    % 파일 읽기
    fileID = fopen(fname, 'r', 'n', 'UTF-8');
    lines = textscan(fileID, '%s', 'Delimiter', '\n');
    fclose(fileID);

    % 불필요한 문자 제거 및 데이터 처리
    lines = strrep(lines{1}, '" "', '0');
    lines = strrep(lines, '"', '');

    % 특정 단어 포함 여부 확인
    target_word = 'Table';
    result = {};

    for i = 1:numel(lines)
        if contains(lines{i}, target_word)
            sub_list = {};
            for j = i+1:min(i+4, numel(lines))
                value = str2double(strsplit(lines{j}, ','));
                value(isnan(value)) = 0;
                sub_list{end+1} = value;
            end
            result{end+1} = vertcat(sub_list{:})';
        end
    end

    % 결과 데이터 반환
    ncoil = result;
end
