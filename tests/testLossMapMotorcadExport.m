% testLossMapMotorcadExport 
%% object make
HDEV_motorcad=MotorcadData(12);
HDEVdata=DataPkBetaMap(HDEV_motorcad.p);
PmsmFem.NumPolePairs = HDEVdata.p/2;


% HDEV_motorcad.motorcadMotPath='Z:\Thesis\Optislang_Motorcad\Validation'
HDEV_motorcad.motocadLabPath=strcat('Z:\01_Codes_Projects\git_Motor_System_Model\Mathworks_ref\HDEV_fluxmodel\HDEV_Model2','\Lab\');
HDEV_motorcad.proj_path=HDEV_motorcad.motorcadMotPath;
HDEV_motorcad.file_path=HDEV_motorcad.proj_path;

HDEV_motorcad.matfileFindList=what(HDEV_motorcad.motocadLabPath);

HDEV_motorcad.file_name='HDEV_Model2';
inputobj=HDEV_motorcad;

%% LabMat Import - ref compMatFile
HDEV_motorcad.proj_path=HDEV_motorcad.motorcadMotPath;
HDEV_motorcad.file_path=HDEV_motorcad.proj_path;

HDEV_motorcad.motocadLabPath=strcat('Z:\01_Codes_Projects\git_Motor_System_Model\Mathworks_ref\HDEV_fluxmodel\HDEV_Model2','\Lab\');
HDEV_motorcad.matfileFindList=what(HDEV_motorcad.motocadLabPath);

% mcad = actxserver('MotorCAD.AppAutomation');
HDEV_motorcad.matfileFindList.mat
i=2
HDEVdata.MotorcadMat=load(fullfile(HDEV_motorcad.motocadLabPath,HDEV_motorcad.matfileFindList.mat{i}))

%% Compute the LossCoefficient 
HDEVdata=HDEVdata.compMatFileLoss()


%% Plot Mat flux from Saturation (High Fidel)

surfLossCoefficient(HDEVdata.phaseVec,HDEVdata.currentVec,HDEVdata.LossMap.HysCoeff)
surfLossCoefficient(HDEVdata.phaseVec,HDEVdata.currentVec,HDEVdata.LossMap.EddyCoeff)

hold on

%%

%% 일괄 Formatter
% 현재 떠 있는 모든 figure의 handle을 얻어옴
figHandles = findobj('Type', 'figure');

num_figures = numel(findall(0,'type','figure'))
for i = 1:num_figures
    figure(figHandles(i))
    formatterSCI_IpkBeta
    % 해당 figure에 대한 format 변경 코드 작성
end



%% 각 figure를 png 형태로 저장
folderPath = 'Z:\01_Codes_Projects\Thesis_skku\Thesis_SKKU\figure'; % 저장할 폴더 경로



for i = 1:length(figHandles)
    figHandle = figHandles(i);
    figAxis=figHandle.Children
    figName = figAxis.Title.String;
    figName = strrep(figName, ' ', '_'); % 공백을 언더바로 변경
    figName = strrep(figName, '.', ''); % '.'을 제거
    filename = fullfile(folderPath, [figName '.png']); % 저장할 파일명과 경로를 합칩니다.
    exportgraphics(figHandle, filename, 'Resolution', 600,'BackgroundColor', 'none');
end
