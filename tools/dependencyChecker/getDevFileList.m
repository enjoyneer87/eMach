function devList=getDevFileList()
fileList=dir;
devList = fileList(contains({fileList.name}, 'dev', 'IgnoreCase', true));
% Remove 'dev' from the file names
tempFileList = strrep({devList.name}, 'dev', '');
tempFileList = strrep(tempFileList, 'Dev', '');
tempFileList = strrep(tempFileList, 'deV', '');

devList=struct2table(devList);
[Dir,~,~]=fileparts(pwd);
devList.FinishedFile=findFilePaths(Dir,tempFileList)';
end