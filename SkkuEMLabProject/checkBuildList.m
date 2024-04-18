%% temp - 전체 인원 데이터
function [BuilListMatFilePath,BuildList]=checkBuildList(refPath,searchType)
if nargin<2
parentPath=fileparts(refPath);
else, strcmp(searchType,'1')
parentPath=refPath;    
end

% addpath(genpath(pwd));  % 현재경로및 하위폴더 경로 추가
% addpath(genpath(parentPath));  % 현재경로및 하위폴더 경로 추가

% parentPath                        ='Z:\Simulation\LabProj2023v1';
MotFileList                                     =findMOTFiles(parentPath)';
MotFileList = removeAutoSaveFiles(MotFileList);
MotFileList =MotFileList';
PNGFileList                                     =findPNGFiles(parentPath)';
engineerList                                    =getSubPathStructList(parentPath)';
% csvFileList                                     =findCSVFiles(parentPath)';
%%  모든 MotFile로부터 Build Check후 mat파일로 export
    if ~isempty(MotFileList)
        BuildList                               = getBuildListFromMotFileList(MotFileList);
        CheckBuildList=makeNewBuildListWithCheckLabBuild(BuildList); 
        BuilListMatFilePath=fullfile(parentPath,"BuildList.mat");
        disp([BuilListMatFilePath,'output is Str Cell List'])
        save(BuilListMatFilePath,"CheckBuildList");
        % engineerList{engineerIndex,2}=BuildList;
        % clear BuildList
    end
end

