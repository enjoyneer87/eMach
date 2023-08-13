function addString2PathName(originalPath,replaceString)
  % 경로를 파일 구분자로 분할
  parts = strsplit(originalPath, filesep);

  % 마지막 부분을 'Design001'으로 변경
  parts{end} =strcat(parts{end},replaceString);

  % 변경된 부분들을 다시 연결
  newPath = strjoin(parts, filesep);

  % 폴더 이름 변경
  status = movefile(originalPath, newPath);

  if status
    disp(['경로가 성공적으로 변경되었습니다: ' newPath]);
  else
    disp('경로 변경에 실패했습니다. 경로가 올바른지 확인하세요.');
  end
end
