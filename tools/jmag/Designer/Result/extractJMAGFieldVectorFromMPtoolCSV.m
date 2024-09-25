function stepdata = extractJMAGFieldVectorFromMPtoolCSV(filename,keywordIndex)
    % 전체 데이터 읽기
    filename=MPToolCSVFilePath
    opts=detectImportOptions(filename)
    data = readtable(filename, opts);

    % 특정 키워드가 포함된 행 찾기
    keywordIndices = find(contains(data.Var1,keywordIndex));

    % 결과를 저장할 구조체 초기화
    stepdata = struct;

    for StepIndex = 1:length(keywordIndices) - 1
        % row 1
        row1Index = keywordIndices(StepIndex);
        Nextrow1Index = keywordIndices(StepIndex + 1);

        % row 2
        row2Index = row1Index + 1;
        row2 = data(row2Index, :);

        step            = row2(:,1).Variables;
        timeStep        = row2(:,2).Variables;
        OutputType      = row2(:,3).Variables;
        PhysicalType    = row2(:,4).Variables;
        ValueType       = row2(:,5).Variables;

        % row 3
        row3Index       = row2Index + 1;
        row3            = data(row3Index, :);
        NumberData =    str2double(row3.Var1);

        % row 4 vector data
        row4Index        = row3Index + 1;
        row4             = data(row4Index:Nextrow1Index - 1, 2:7);
        row4ID           = data(row4Index:Nextrow1Index - 1, 1);
        % 나머지 행을 숫자로 변환
        numericData = table2array(row4);

        % 변수 이름 설정
        if ValueType == 1
            row4VarName = {'ElementIDorNodeID', 'xCoordi', 'yCoordi', 'zCoordi', 'vecx', 'vecy', 'vecz', 'vecxIm', 'vecyIm', 'veczIm'};
        else
            if OutputType == 4
                row4VarName = {'ElementID', 'xCoordi', 'yCoordi', 'zCoordi', 'vecx', 'vecy', 'vecz'};
            elseif OutputType == 1
                % row4VarName = {'NodeID', 'xCoordi', 'yCoordi', 'zCoordi', 'vecx', 'vecy', 'vecz'};
                row4VarName = {'NodeID', 'PosX', 'PosY', 'PosZ', 'vecx', 'vecy', 'vecz'};

            end
        end

        % 숫자 데이터로 테이블 생성
        dataTable = array2table(numericData(:, 1:length(row4VarName)-1), 'VariableNames', row4VarName(2:end));
        dataTable = [row4ID dataTable];
        dataTable.Properties.VariableNames{1}=row4VarName{1};
        % step 데이터 저장
        stepdata.(['step', step{:}]) = dataTable;
    end
end