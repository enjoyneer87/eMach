function newPath = changeLastPartOfPath(originalPath,replaceString)
  parts = strsplit(originalPath, filesep); % 경로를 파일 구분자로 분할
  parts{end} = replaceString; % 마지막 부분을 'Design001'으로 변경
  newPath = strjoin(parts, filesep); % 변경된 부분들을 다시 연결
end