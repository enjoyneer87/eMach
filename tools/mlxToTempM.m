function mlxToTempM(folderPath)
    % 폴더 경로가 제공되지 않은 경우 현재 디렉토리를 사용
    if nargin < 1
        folderPath = pwd; % 현재 작업 디렉토리
    end
    
    % 폴더 내의 모든 .mlx 파일 검색
    mlxFiles = dir(fullfile(folderPath, '*.mlx'));
    
    % 각 .mlx 파일에 대해 반복
    for k = 1:length(mlxFiles)
        % 원본 .mlx 파일 이름
        mlxFileName = mlxFiles(k).name;
        % 새 .m 파일 이름 생성 ('temp' 접두어 추가)
        mFileName = [mlxFileName(1:end-4), '.m'];
        
        % .mlx 파일을 .m 파일로 변환
        % MATLAB R2019b 이상에서 지원하는 matlab.internal.liveeditor.openAndConvert 함수 사용
        try
            matlab.internal.liveeditor.openAndConvert(fullfile(folderPath, mlxFileName), fullfile(folderPath, mFileName));
            fprintf('Converted %s to %s\n', mlxFileName, mFileName);
        catch ME
            warning('Failed to convert %s: %s', mlxFileName, ME.message);
        end
    end
end
