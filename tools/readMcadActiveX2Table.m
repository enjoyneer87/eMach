function ActiveXParameters = readMcadActiveX2Table(fileName)
    % readMcadActiveX2Table: 파일에서 ActiveX 매개변수를 읽어 테이블로 반환하는 함수
    
    % 파일로부터 초기 가져오기 옵션을 감지합니다
    opts = detectImportOptions(fileName);
    
    % 변수 이름을 순회하며 변수 형식을 수정합니다
    for i = 1:length(opts.VariableNames)
        if strcmp(opts.VariableNames{i}, 'Input_Output')
            opts.VariableTypes{i} = 'categorical';
        end
        
        if strcmp(opts.VariableNames{i}, 'Units')
            opts.VariableTypes{i} = 'categorical';
        end
        
        if strcmp(opts.VariableNames{i}, 'CurrentValue')
            opts.VariableTypes{i} = 'char';
        end
        
        if strcmp(opts.VariableNames{i}, 'DefaultValue')
            opts.VariableTypes{i} = 'char';
        end
        
        if strcmp(opts.VariableNames{i}, 'DataType')
            opts.VariableTypes{i} = 'categorical';
        end
    end
    
    % 수정된 변수 형식을 사용하여 데이터를 테이블로 읽어옵니다
    ActiveXParameters = readtable(fileName, opts);
    
    %% _ 로 변경
    ActiveXParameters.Category = strrep(ActiveXParameters.Category, ' ', '_');
    ActiveXParameters.Category = strrep(ActiveXParameters.Category, '(', '_');
    ActiveXParameters.Category = strrep(ActiveXParameters.Category, ')', '_');
    ActiveXParameters.Category = strrep(ActiveXParameters.Category, '-', '');

    % ActiveXParameters의 Category의 categorical 화
    ActiveXParameters.Category = categorical(ActiveXParameters.Category);
end
