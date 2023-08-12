%% temp - 전체 인원 데이터
addpath(genpath(pwd));  % 현재경로및 하위폴더 경로 추가

parentPath                        ='Z:\Simulation\LabProj2023v1';
MotFileList                                     =findMOTFiles(parentPath);
MotFileList                                     =MotFileList';
csvFileList                                     =findCSVFiles(parentPath);
csvFileList                                     =csvFileList';
PNGFileList                                     =findPNGFiles(parentPath);
PNGFileList                                     =PNGFileList';
engineerList                                    =getSubPathStructList(parentPath);
engineerList                                     ={engineerList.name}';

for engineerIndex= 1:numel(engineerList)
    engineerList{engineerIndex,1}= fullfile(parentPath, engineerList{engineerIndex});
end
engineerList{1,2}=[];

%% 해당 인원 해석 폴더 설정
for engineerIndex=4:numel(engineerList)
    %% refFile
    addPathWithSubPath(engineerList{engineerIndex})
    refPath =fullfile(engineerList{engineerIndex},'MCAD');
    %% Mot File 찾기
    existingDoeFolder=fullfile(engineerList{engineerIndex},'DOE');
    if exist(existingDoeFolder,"dir")
        MotFileList                             =findMOTFiles(existingDoeFolder);    
        MotFileList =MotFileList';
    end
    % AutoSave 제외 
    MotFileList = removeAutoSaveFiles(MotFileList);

    %%  모든 MotFile로부터 Build Check후 mat파일로 export
    if ~isempty(MotFileList)
        BuildList                                   = getBuildListFromMotFileList(MotFileList);
        save(fullfile(engineerList{engineerIndex},"BuildList.mat"),"BuildList");
        engineerList{engineerIndex,2}=BuildList;
        clear BuildList
    end
end
