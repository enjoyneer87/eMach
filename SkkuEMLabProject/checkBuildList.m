%% temp - 전체 인원 데이터
function [BuilListMatFilePath,BuildList]=checkBuildList(refPath,searchType)
if nargin<2
parentPath=fileparts(refPath);
else, strcmp(searchType,'1')
parentPath=refPath;    
end

addpath(genpath(pwd));  % 현재경로및 하위폴더 경로 추가
addpath(genpath(parentPath));  % 현재경로및 하위폴더 경로 추가

% parentPath                        ='Z:\Simulation\LabProj2023v1';
MotFileList                                     =findMOTFiles(parentPath);
MotFileList                                     =MotFileList';
csvFileList                                     =findCSVFiles(parentPath);
csvFileList                                     =csvFileList';
PNGFileList                                     =findPNGFiles(parentPath);
PNGFileList                                     =PNGFileList';
engineerList                                    =getSubPathStructList(parentPath);
engineerList                                     ={engineerList.name}';
% 
% for engineerIndex= 1:numel(engineerList)
%     engineerList{engineerIndex,1}= fullfile(parentPath, engineerList{engineerIndex});
% end
% engineerList{1,2}=[];

%% 해당 인원 해석 폴더 설정
% for engineerIndex=4:4
%     %% refFile
%     addPathWithSubPath(engineerList{engineerIndex})
%     refPath =fullfile(engineerList{engineerIndex},'MCAD');
%     %% Mot File 찾기
%     existingDoeFolder=fullfile(engineerList{engineerIndex},'DOE');
%     if exist(existingDoeFolder,"dir")
%         MotFileList                             =findMOTFiles(existingDoeFolder);    
%         MotFileList =MotFileList';
%     end
    % AutoSave 제외 
    MotFileList = removeAutoSaveFiles(MotFileList);
    MotFileList =MotFileList';
    %%  모든 MotFile로부터 Build Check후 mat파일로 export
    if ~isempty(MotFileList)
        BuildList                                   = getBuildListFromMotFileList(MotFileList);
        BuilListMatFilePath=fullfile(parentPath,"BuildList.mat");
        disp([BuilListMatFilePath,'output is Str Cell List'])
        save(BuilListMatFilePath,"BuildList");
        % engineerList{engineerIndex,2}=BuildList;
        % clear BuildList
    end
end

