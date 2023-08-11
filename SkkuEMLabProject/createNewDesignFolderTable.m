function newDesignFolderTable = createNewDesignFolderTable(refMotFilePath,DoETable)
    % DoETable의 길이를 얻어옴
    numFolders = height(DoETable);
    
    % 테이블 초기화
    newDesignFolderTable = table('Size', [numFolders, 1], 'VariableTypes', {'string',}, 'VariableNames', {'DesignFolderPath'});
    
    % 각 케이스에 대한 새 폴더 경로 생성 및 테이블에 추가
    for CaseNumber = 1:numFolders
        newFolder = createNewFolder(refMotFilePath, CaseNumber);    % 새 폴더 경로 생성
        newDesignFolderTable.DesignFolderPath(CaseNumber) = newFolder;  % 테이블에 새 폴더 경로 추가
    end
end
