function [CoilTable,CoilStruct] = readJmagWindingPatternCSV()
    % windingPattternCSVPath: CSV 파일 경로
    windingPattternCSVPath='Z:\Thesis\00_Theory_Prof\JFTZIP\JFT145WindingEditorParallel\JFT145WindingEditorParallel\JFT145WindingEditorParallel_B-01.csv'
    % windingPattternCSVPath='Z:\Thesis\00_Theory_Prof\JFTZIP\JFT148CoilWindingOption\JFT148CoilWindingOption-01.csv';

    % CSV 파일 읽기
    delimiter = ',';  % CSV 파일 구분자 설정
    % opts = detectImportOptions(windingPattternCSVPath);

    opts = detectImportOptions(windingPattternCSVPath, 'Delimiter', delimiter,'VariableNamingRule','modify');
    VariableTypes      = repmat({'char'}, 1, length(opts.VariableTypes));
    opts.VariableTypes=VariableTypes;

    % opts.TextType = 'string';  % 모든 데이터를 문자열로 읽어들이도록 설정
    data = readtable(windingPattternCSVPath,opts);

    % 'Table'로 시작하는 행의 인덱스 찾기
    readPropertiesTable = data(1:2,:);
    NameIndices = find(contains(data{:,1}, 'Name'));
    TableIndices = find(contains(data{:,1}, 'Table'));

    for TableIndex = 1:length(TableIndices)
    %% CoilInfo
    % {'ReadPropertiesTab' }    {'0'      }  
    % {'NumCoils'          }    {'24'     }  
    % {'Name_1'            }    {'コイル 1'}  
    % {'PhaseIndex_1'      }    {'0'      }  
    % {'SerialGroupIndex_1'}    {'0'      }  
        CoilStruct(TableIndex).CoilInfo = data(NameIndices(TableIndex):[TableIndices(TableIndex)],:);
    % CoilTable    
        if TableIndex == length(TableIndices)
            CoilStruct(TableIndex).SlotLayerTable = data(TableIndices(TableIndex)+1:end,:);
        else
            CoilStruct(TableIndex).SlotLayerTable = data(TableIndices(TableIndex)+1:NameIndices(TableIndex+1)-1,:);
        end
    end


    %% 새로운 테이블 생성
    CoilTable = table();
    % Coil 정보 추가
    for i = 1:length(CoilStruct)
        % Coil 이름 추가
        % newTable = [newTable; {'Name'}, {''}; {'table'}, {''}];        
        % Coil 정보 행 추가
        CoilTable = [CoilTable;CoilStruct(i).CoilInfo];
        % CoilStruct(i).SlotLayerTable=CoilStruct(i).SlotLayerTable{:,:};
        % SlotLayerTable 추가
        CoilTable = [CoilTable; CoilStruct(i).SlotLayerTable];
    end
    CoilTable=[readPropertiesTable;CoilTable];
    % 
    % %% Post Type 2 MCAD
    % for PhaseIndex = 1:length(TableIndices)
    %     CoilStruct(PhaseIndex).SlotLayerDataCell=table2cell(CoilStruct(PhaseIndex).SlotLayerTable)';
    % end

end