function copyPNGFilesToPNGFolder(PNGFileList, PNGFolder)
    % PNG 폴더가 존재하지 않으면 생성
    if ~exist(PNGFolder, 'dir')
        mkdir(PNGFolder);
    end

    % PNGFileList의 각 파일을 PNG 폴더로 복사
    for i = 1:numel(PNGFileList)
        srcFile = PNGFileList{i};
        
        % 파일명에서 확장자 추출
        [~, fileName, ext] = fileparts(srcFile);
        
        % 파일이 PNG 파일인지 확인
        if strcmpi(ext, '.png')
            % 상위 폴더 경로 추출
            parentPath = (fileparts(srcFile));
            
            % 상위 폴더명에서 디자인 번호 추출
            designNumber = extractDesignNumber(parentPath);
            
            % 디자인 번호를 파일명에 추가
            if ~isempty(designNumber) && ~contains(fileName, designNumber)
                fileName = [fileName, '_', designNumber];
            end
            
            % 파일 복사
            destFile = fullfile(PNGFolder, [fileName, '.png']);
            copyfile(srcFile, destFile);
        end
    end
end