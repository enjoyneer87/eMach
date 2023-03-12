%% MotorCADData object make temp=65
HDEVMotorCADTemp65=MotorcadData(12);
HDEVMotorCADTemp65.motorcadMotPath='Z:\Thesis\Optislang_Motorcad\Validation'
HDEVMotorCADTemp65.motocadLabPath=strcat('Z:\01_Codes_Projects\git_Motor_System_Model\Mathworks_ref\HDEV_fluxmodel\HDEV_Model2','\Lab\');
HDEVMotorCADTemp65.proj_path=HDEVMotorCADTemp65.motorcadMotPath;
HDEVMotorCADTemp65.file_path=HDEVMotorCADTemp65.proj_path;
HDEVMotorCADTemp65.matfileFindList=what(HDEVMotorCADTemp65.motocadLabPath);
HDEVMotorCADTemp65.file_name='HDEV_Model2';




% temp=115

global phasemesh
global currentmesh
% %% Raw PsiDModel_Lab import - ModelParameters_MotorLAB- 
% HDEVMotorCADTemp65.ModelParameters_MotorLAB
% HDEVMotorCADTemp65=HDEVMotorCADTemp65.rawPsiDataPost()
% % 115
% HDEVMotorCADTemp115.ModelParameters_MotorLAB
% HDEVMotorCADTemp115=HDEVMotorCADTemp115.rawPsiDataPost()
% %% postMotorCADData object make temp=115
% HDEVMotorCADTemp115post = ResultMotorcadLabData(HDEVMotorCADTemp65);
% 
% HDEVMotorCADTemp115post.postMagnet_Temperature=115
% HDEVMotorCADTemp115post.postArmatureConductor_Temperature=115
% HDEVMotorCADTemp115post=HDEVMotorCADTemp115post.tempCorrectedModelParameters_MotorLAB(-0.12)
% 

%% Same as  Raw PsiModel_Lab Current Vector 
HDEVdata=DataPkBetaMap(HDEVMotorCADTemp65.p);
%%currentVec
NcurrentVec=5
currentMax=1000;
currentVec=[0:currentMax/(NcurrentVec):currentMax]'
phaseMax=90;
NphaseVec=5
phaseVec=[0:phaseMax/(NphaseVec-1):phaseMax];
HDEVdata.phaseVec=phaseVec;
HDEVdata.currentVec=currentVec;
%% mesh for Psi data 
PmsmFem.NumPolePairs = HDEVdata.p/2;
currentmesh = repmat(HDEVdata.currentVec,1,length(phaseVec))
% size(currentmesh)
phasemesh = repmat(HDEVdata.phaseVec,length(currentmesh),1)

% size(phasemesh)

%% LabMat Import - ref compMatFile
HDEVMotorCADTemp65.proj_path=HDEVMotorCADTemp65.motorcadMotPath;
HDEVMotorCADTemp65.file_path=HDEVMotorCADTemp65.proj_path;

HDEVMotorCADTemp65.motocadLabPath=strcat('Z:\01_Codes_Projects\git_Motor_System_Model\Mathworks_ref\HDEV_fluxmodel\HDEV_Model2','\Lab\');
HDEVMotorCADTemp65.matfileFindList=what(HDEVMotorCADTemp65.motocadLabPath);

% mcad = actxserver('MotorCAD.AppAutomation');
HDEVMotorCADTemp65.matfileFindList.mat
i=7
HDEVdata.MotorcadMat=load(HDEVMotorCADTemp65.matfileFindList.mat{i})
HDEVdata=HDEVdata.compMatiFilePsi()

%% Plot Mat flux from Saturation (High Fidel)

figure(1)
ax=gca;
surf( HDEVdata.MotorcadMat.Phase_Advance(1,:), HDEVdata.MotorcadMat.Stator_Current_Line_Peak(:,1),HDEVdata.flux_linkage_map.in_d,'DisplayName','Surface@115degfrom85deg')
ax.ZLabel.String='Flux Linkage[Vs]'
ax.Parent.Name='\Psi_D'
formatterSCI_IpkBeta
legend('Location', 'best');

hold on
% scatter3(matData.Phase_Advance,matData.Stator_Current_Line_Peak,flux1D,'red')

figure(2)
ax=gca;
surf( HDEVdata.MotorcadMat.Phase_Advance(1,:), HDEVdata.MotorcadMat.Stator_Current_Line_Peak(:,1),HDEVdata.flux_linkage_map.in_q,'DisplayName','Surface@115degfrom85deg')
ax.ZLabel.String='Flux Linkage[Vs]'
ax.Parent.Name='\Psi_Q'
formatterSCI_IpkBeta
legend('Location', 'best');

hold on
% scatter3(matData.Phase_Advance,matData.Stator_Current_Line_Peak,flux1Q,'red')


% 
% 
% filename = fullfile(folderPath, ['TempFluxlinkage.png']); % 저장할 파일명과 경로를 합칩니다.
% exportgraphics(figHandle, filename, 'Resolution', 600,'BackgroundColor', 'none');





[refTempMotorcad calcTempMotorcad refTempMotorcadPost] =plotScatter3TempPost('HDEV_Model2',1,'HDEV_Model2Temp115')
hold on



figHandles = findobj('Type', 'figure');

% 각 figure의 모든 subfigure 객체 호출
for i = 1:length(figHandles)
    figHandle = figHandles(i);
    figChildren = get(figHandle, 'Children');
    formatterSCI_IpkBeta
    folderPath = 'Z:\01_Codes_Projects\Thesis_skku\Thesis_SKKU\figure'; % 저장할 폴더 경로
    figName=figHandle.Name
    figAxis=figHandle.Children;
%     figName = strrep(figName, ' ', '_'); % 공백을 언더바로 변경
%     figName = strrep(figName, '.', ''); % '.'을 제거
    filename = fullfile(folderPath, [figName 'TempFluxlinkage.png']); % 저장할 파일명과 경로를 합칩니다.
    exportgraphics(figHandle, filename, 'Resolution', 600,'BackgroundColor', 'none');

end

