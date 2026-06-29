function modifiedData=getDataFromMotFiles(MotFilePath)
%% GETDATAFROMMOTFILES (Wrapper)
%
%   This is a backward-compatible wrapper. The actual implementation
%   is now located in the namespace package mcad.getDataFromMotFiles.

modifiedData = mcad.getDataFromMotFiles(MotFilePath);
end