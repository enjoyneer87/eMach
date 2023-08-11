function newDesignFolderTable = createDoECheckTable(refMotFilePath, DoETable)
    % 디자인 폴더 경로 테이블 생성
    newDesignFolderTable = createNewDesignFolderTable(refMotFilePath, DoETable);
    
    % BuildStatus 열 초기화
    newDesignFolderTable = setDefaultBuildStatus(newDesignFolderTable);
end