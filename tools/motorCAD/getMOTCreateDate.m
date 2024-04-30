function MotFileDate=getMOTCreateDate(MotFilePath)
%% Mot FileData
% % MotFiles      =findMOTFiles(NewMotFileDIR);
% 
% NewMotFileDIR=fileparts(MotFileList{MotFileIndex})
% files         =dir(NewMotFileDIR);
% MotFileIndex  =contains({files.name},'.mot');
% % MotFileDate   =files(MotFileIndex).date;
% 
% % 파일 경로 지정
% MotFilePath = fullfile(NewMotFileDIR,files(MotFileIndex).name);
creationDate= getFileCreationDate(MotFilePath);
MotFileDate = mkDateTimeType(creationDate);
end
