function newTable = setDefaultBuildStatus(DesignFolderTable)
    % BuildStatus 변수열의 기본값을 0으로 설정해주는 함수
    
    % 입력 테이블 복사
    newTable         = DesignFolderTable;
    motFileName  = repmat("",height(newTable),1);
    motFile      = repmat("",height(newTable),1);
    % BuildStatus 변수열의 모든 값을 0으로 설정
    for i = 1:height(newTable)
        parts=strsplit(newTable.DesignFolderPath(i),filesep);
        motFileName(i) = parts{end};
        motFile(i)  = strcat(motFileName(i),".mot"); % DesignFolder에 .mot 확장자 추가
    end
    
    % BuildStatus 변수열의 모든 값을 0으로 설정
    newTable.motFileName                = motFileName;           % 파일 이름 목록(Mot파일 결과 폴더이기도함)
    newTable.motFile                    = motFile;               % 파일 목록
    newTable.motFilePathCheck(:)        = categorical(0);        % 파일 생성 시 체크
    newTable.GeometryCheck(:)           = categorical(0);        % Geometry 여부로 체크
    newTable.BuildStatusCheckByPath(:)  = categorical(0);        % Lab Folder 여부로 체크
    newTable.BuildStatusCheckByMCAD(:)  = categorical(0);        % MOT File 열어서 스크립트로 확인

    %% MAP 데이터 추출
    
end
