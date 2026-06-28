
% mlx2livem.m
% .mlx -> Live Code File (.m) 변환 후 원본 .mlx 삭제
% matlab.internal.liveeditor.openAndConvert 사용 (미문서화 내부 함수)
% * 실행 전 targetFolder 를 워크스페이스에서 정의해두거나 아래 주석 해제

% % 대상 폴더 (필요하면 절대경로로 바꿔쓰세요)
% targetFolder = fullfile(pwd);
%
% if ~isfolder(targetFolder)
%     error('Target folder does not exist: %s', targetFolder);
% end

mlxFiles = findAnyFiles(targetFolder, '.mlx');
if isempty(mlxFiles)
    fprintf('No .mlx files found in %s\n', targetFolder);
    return
end

fprintf('Found %d .mlx file(s).\n', numel(mlxFiles));

for k = 1:numel(mlxFiles)
    mlxPath = mlxFiles{k};
    [mlxDir, nameOnly] = fileparts(mlxPath);
    mlxName = [nameOnly, '.mlx'];
    mName   = [nameOnly, '.m'];
    mPath   = fullfile(mlxDir, mName);

    fprintf('Processing: %s -> %s ... ', mlxName, mName);

    converted = false;

    % --- Live Code .m 변환 시도 (버전별 내부 함수 우선순위) ---
    try
        if exist('matlab.internal.liveeditor.openAndConvert', 'file')
            matlab.internal.liveeditor.openAndConvert(mlxPath, mPath);
            converted = true;
            fprintf('converted (liveeditor). ');
        elseif exist('matlab.internal.richeditor.openAndConvert', 'file')
            matlab.internal.richeditor.openAndConvert(mlxPath, mPath);
            converted = true;
            fprintf('converted (richeditor). ');
        else
            error('matlab.internal.liveeditor.openAndConvert not found in this MATLAB version.');
        end
    catch err
        fprintf('FAILED.\n  Error: %s\n', err.message);
    end

    % --- 변환 성공 시 원본 .mlx 삭제 ---
    if converted && isfile(mPath)
        try
            delete(mlxPath);
            fprintf('Deleted original .mlx\n');
        catch delErr
            warning('Converted but failed to delete %s: %s', mlxPath, delErr.message);
        end
    else
        fprintf('Skipped deletion.\n');
    end
end

fprintf('Done.\n');
