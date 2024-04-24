function deleteDir(folderPath)

% 폴더 경로 지정

% 폴더 삭제
try
    rmdir(folderPath, 's');  % 's' 옵션은 폴더와 그 내용을 모두 삭제합니다.
    disp(['Folder deleted successfully: ', folderPath]);
catch ME
    disp(['Error deleting folder: ', ME.message]);
end

end