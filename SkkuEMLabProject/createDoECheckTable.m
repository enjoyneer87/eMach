function newDesignFolderTable = createDoECheckTable(refMotFilePath, DoETable, Type)
    % 디자인 폴더 경로 테이블 생성
    MotFileList                       =findMOTFiles(fileparts(refMotFilePath));
    removeAutoSaveFiles(MotFileList)
    if nargin == 3
        newDesignFolderTable = createNewDesignFolderTable(refMotFilePath, DoETable, Type);
    elseif nargin == 2
        newDesignFolderTable = createNewDesignFolderTable(refMotFilePath, DoETable);
    else
        error('Invalid number of input arguments.');
    end
    
    % BuildStatus 열 초기화
    newDesignFolderTable = setDefaultBuildStatus(newDesignFolderTable);
end
