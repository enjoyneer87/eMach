function newDesignFolderTable = createNewDesignFolderFromTable(refMotFilePath, DoETable, Type)
    % DoETable의 길이를 얻어옴
    numFolders = height(DoETable);
    
    % 테이블 초기화
    newDesignFolderTable = table('Size', [numFolders, 1], 'VariableTypes', {'string',}, 'VariableNames', {'DesignFolderPath'});

    % Type 값에 따라 다른 동작 수행
    if nargin < 3 || (ischar(Type) && strcmpi(Type, 'matlab')) || (isnumeric(Type) && Type == 0)
        % 각 케이스에 대한 새 폴더 경로 생성 및 테이블에 추가
        for CaseNumber = 1:numFolders
            newFolder = createNewFolder(refMotFilePath, CaseNumber);    % 새 폴더 경로 생성
            newDesignFolderTable.DesignFolderPath(CaseNumber) = newFolder;  % 테이블에 새 폴더 경로 추가
        end
    elseif (ischar(Type) && strcmpi(Type, 'optislang')) || (isnumeric(Type) && Type == 1)
        % dev Make Existing from Optislang DOE
        for CaseNumber = 1:numFolders
            newFolder = createNewDesignFolder(refMotFilePath, CaseNumber);    % 새 폴더 경로 생성
            newDesignFolderTable.DesignFolderPath(CaseNumber) = newFolder;  % 테이블에 새 폴더 경로 추가
        end
    else
        error('Invalid value for Type parameter.');
    end
end
