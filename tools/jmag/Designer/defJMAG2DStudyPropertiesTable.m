function propertiesTable=defJMAG2DStudyPropertiesTable(StudyProperties)
    % Study           =app.GetCurrentStudy;
    % StudyProperties =Study.GetStudyProperties();
    JmagPropertyTableFormat=StudyProperties.GetPropertyTable();
    % 데이터 샘플과 카테고리컬 리스트 선언
    categoricalList = {'Flag', 'Double', 'Coordinate System', 'Table','String'}; % 카테고리컬 변수 목록
    
    % '\n'으로 문자열 분리
    rows = strsplit(JmagPropertyTableFormat, '\n');
    
    
    % 빈 셀 배열 생성
    dataCells = cell(numel(rows), 3);

    for i = 1:numel(rows)
        currentRow = rows{i};
        categoryFound = false;
        
        % 카테고리컬 리스트 검사
        for j = 1:numel(categoricalList)
            category = categoricalList{j};
            if contains(currentRow, category)
                % 카테고리 발견 시 2번째 열에 할당하고 원본 문자열에서 제거
                dataCells{i, 2} = category;
                currentRow = strrep(currentRow, category, '');
                categoryFound = true;
                break; % 카테고리는 한 행에 하나만 있다고 가정
            end
        end
        
        if ~categoryFound
            error('No category found in the row.');
        end
        
        % 남은 문자열을 ' '로 분리
        splitData = strtrim(strsplit(currentRow, ' ')); % strtrim을 사용해 앞뒤 공백 제거
      
        % 첫 번째 열과 다섯 번째 열 할당
        dataCells{i, 1} = splitData{1}; % 첫 번째 요소는 첫 번째 열에 할당
        if numel(splitData) > 1
            dataCells{i, 5} = strjoin(splitData(2:end), ' '); % 나머지 요소는 세 번째 열에 할당
        else
            dataCells{i, 5} = '';
        end
        % propertiesValue는 비워둠
        dataCells{i, 3} = ''; 
        % double Type의 Unit 비워둠
        dataCells{i, 4} = '';   
        % Flag Type의 Key값 옵션
        KeyOptions=[];
        KeyNames=StudyProperties.GetKeyNames(dataCells{i,1})';
        for KeyIndex=1:length(KeyNames)
            KeyDescription =  StudyProperties.GetFlagPropertyHelp(dataCells{i,1},KeyIndex-1);
            KeyOptions=[KeyOptions '[' KeyNames{KeyIndex}, ':',KeyDescription,']'];
        end    
        dataCells{i,6} = KeyOptions;
    end
    
    % 셀 배열을 테이블로 변환
        propertiesTable = cell2table(dataCells, 'VariableNames', ...
                                     {'propertiesName','Category', 'PropertiesValue(KeyValue)', 'Unit','description', 'KeyOption'});
    
    % dataCells = dataCells(~cellfun('isempty', dataCells));

end
