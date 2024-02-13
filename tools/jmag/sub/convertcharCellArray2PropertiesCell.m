function resultCell = convertcharCellArray2PropertiesCell(inputCell)
    % 입력으로 주어진 셀 배열을 처리하여 반환하는 함수

    % 첫번째 행
    resultCell{1} = inputCell{1};

    % 두번째 행
    resultCell{2} = inputCell{2};

    % 세번째부터 마지막 행
    charData = ''; % 빈 문자열 초기화

    for i = 3:length(inputCell)
        charData = [charData inputCell{i} ' ']; % 각 행의 데이터를 공백 추가하여 합침
    end

    % 3번째 행에 합쳐진 char 데이터 추가
    resultCell{3} = charData;

    % 3번째 행 이후의 데이터 삭제
    resultCell(4:end) = [];
end
