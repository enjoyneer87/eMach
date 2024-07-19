function [BuildList, MotFileParentPath] = mkMCADScaledFilesFromList(BuildList, AddName, parentPath)
    if ~isstruct(BuildList)
        if istable(BuildList)
        BuildList=table2struct(BuildList);
        end
    end
    % 병렬 풀 설정
    if isempty(gcp('nocreate'))
        parpool;  % 기본 설정으로 병렬 풀 시작
    end
    
    
    % 출력 파일 경로 설정
    MotFileParentPath = fullfile(parentPath, AddName);
    
    % 병렬 처리를 위한 parfor 루프
    parfor MotFileIndex = 1:length(BuildList)
        refModelPath = BuildList(MotFileIndex).MotFilePath;
        SLFEAMotFilePath = mkMCADFileFromRefPath(refModelPath, AddName);
        BuildList(MotFileIndex).([AddName, 'MotFilePath']) = SLFEAMotFilePath;
    end
    
    BuildList=struct2table(BuildList);
end
