function [BuildList, MotFileParentPath] = mkMCADScaledFilesFromList(BuildList, AddName, parentPath)
    % 병렬 풀 설정
    if isempty(gcp('nocreate'))
        parpool;  % 기본 설정으로 병렬 풀 시작
    end
    
    % 출력 파일 경로 설정
    % AddName='SLLAW'
    MotFileParentPath = fullfile(parentPath, AddName);
    
    % 병렬 처리를 위한 parfor 루프
    parfor MotFileIndex = 1:length(BuildList)
        refModelPath = BuildList(MotFileIndex).MotFileName;
        SLFEAMotFilePath = mkMCADFileFromRefPath(refModelPath, AddName);
        BuildList(MotFileIndex).([AddName, 'MotFilePath']) = SLFEAMotFilePath;
    end

end
