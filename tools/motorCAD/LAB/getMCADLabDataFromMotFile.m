function filteredTable=getMCADLabDataFromMotFile(ActiveXParametersStruct,txtDir)
%% GETMCADLABDATAFROMMOTFILE (Wrapper)
%
%   This is a backward-compatible wrapper. The actual implementation
%   is now located in the namespace package mcad.getMCADLabDataFromMotFile.

if nargin < 2, txtDir = []; end
filteredTable = mcad.getMCADLabDataFromMotFile(ActiveXParametersStruct, txtDir);
end
% p(@plotFitResult, filteredTable);
% 비교대상
% devSatuaMapTable2TXTinLabLinkFormat(newScaledTable,satuMap4.BuildingData.MotorCADGeo,pwd);