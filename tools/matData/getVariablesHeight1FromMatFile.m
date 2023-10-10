function varNamesCell = getVariablesHeight1FromMatFile(matFileName)
    % matfile 객체 생성
    matObj = matfile(matFileName);

    % MAT 파일에 저장된 모든 변수 정보를 가져오기
    varInfo = whos(matObj);

    % 높이가 1인 변수명만 저장할 셀 배열 초기화
    varNamesCell = {};

    % 높이가 1인 변수명 구하기
    for i = 1:numel(varInfo)
        if varInfo(i).size(1) == 1
            varNamesCell{end+1} = varInfo(i).name;
        end
    end
    varNamesCell=varNamesCell';
end
