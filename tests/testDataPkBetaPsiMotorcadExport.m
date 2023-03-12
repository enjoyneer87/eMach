%% MotorCADData object make temp=65
HDEVMotorCADTemp65=MotorcadData(12);
HDEVMotorCADTemp65.motorcadMotPath='Z:\Thesis\Optislang_Motorcad\Validation'
HDEVMotorCADTemp65.motocadLabPath=strcat('Z:\01_Codes_Projects\git_Motor_System_Model\Mathworks_ref\HDEV_fluxmodel\HDEV_Model2','\Lab\');
HDEVMotorCADTemp65.proj_path=HDEVMotorCADTemp65.motorcadMotPath;
HDEVMotorCADTemp65.file_path=HDEVMotorCADTemp65.proj_path;
HDEVMotorCADTemp65.matfileFindList=what(HDEVMotorCADTemp65.motocadLabPath);
HDEVMotorCADTemp65.file_name='HDEV_Model2';

%% Raw PsiDModel_Lab import(should do manually) - ModelParameters_MotorLAB- 
HDEVMotorCADTemp65.ModelParameters_MotorLAB
HDEVMotorCADTemp65=HDEVMotorCADTemp65.rawPsiDataPost()
% inputobj=inputobj.rawPsiDataPost() %manual

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

%% plot Psi point Lab 
subplot(1,2,1)
% % surf(HDEVdata.phaseVec,HDEVdata.currentVec,HDEVMotorCADTemp65.ModelParameters_MotorLAB.PsiDModel_Lab)
% currentmesh_col1 = currentmesh(:, 1);
% scatter3(phasemesh', currentmesh', (HDEVMotorCADTemp65.ModelParameters_MotorLAB.PsiDModel_Lab)', ...
%     'DisplayName', num2str(currentmesh_col1));
% hold on

hold on
for i = 1:size(currentmesh, 1)
    scatter3(phasemesh(i,:)', currentmesh(i,:)', HDEVMotorCADTemp65.ModelParameters_MotorLAB.PsiDModel_Lab(i,:)', 'DisplayName', strcat('i=',num2str(currentmesh(i,1)),'@Temp',num2str(HDEVMotorCADTemp65.Magnet_Temperature)))
end
legend('show')
xlabel('Phase')
ylabel('Current')
zlabel('PsiD')
subplot(1,2,2)

surf(HDEVdata.phaseVec,HDEVdata.currentVec,HDEVMotorCADTemp65.ModelParameters_MotorLAB.PsiQModel_Lab)
scatter3(phasemesh,currentmesh,HDEVMotorCADTemp65.ModelParameters_MotorLAB.PsiQModel_Lab,'blue')
hold on

%% LabMat Import - ref compMatFile
HDEVMotorCADTemp65.proj_path=HDEVMotorCADTemp65.motorcadMotPath;
HDEVMotorCADTemp65.file_path=HDEVMotorCADTemp65.proj_path;

HDEVMotorCADTemp65.motocadLabPath=strcat('Z:\01_Codes_Projects\git_Motor_System_Model\Mathworks_ref\HDEV_fluxmodel\HDEV_Model2','\Lab\');
HDEVMotorCADTemp65.matfileFindList=what(HDEVMotorCADTemp65.motocadLabPath);

% mcad = actxserver('MotorCAD.AppAutomation');
HDEVMotorCADTemp65.matfileFindList.mat
i=2
HDEVdata.MotorcadMat=load(HDEVMotorCADTemp65.matfileFindList.mat{i})
HDEVdata=HDEVdata.compMatiFilePsi()

%% Plot Mat flux from Saturation (High Fidel)

subplot(1,2,1)
ax=gca;
surf( HDEVdata.MotorcadMat.Phase_Advance(1,:), HDEVdata.MotorcadMat.Stator_Current_Line_Peak(:,1),HDEVdata.flux_linkage_map.in_d)
ax.ZLabel.String='Flux Linkage[Vs]'
title('\Psi_D')
% hold on
% scatter3(matData.Phase_Advance,matData.Stator_Current_Line_Peak,flux1D,'red')
subplot(1,2,2)
ax=gca;
surf( HDEVdata.MotorcadMat.Phase_Advance(1,:), HDEVdata.MotorcadMat.Stator_Current_Line_Peak(:,1),HDEVdata.flux_linkage_map.in_q)
ax.ZLabel.String='Flux Linkage[Vs]'
title('\Psi_Q')
hold on
% scatter3(matData.Phase_Advance,matData.Stator_Current_Line_Peak,flux1Q,'red')




figHandles = findobj('Type', 'figure');

% 각 figure의 모든 subfigure 객체 호출
for i = 1:length(figHandles)
    figHandle = figHandles(i);
    figChildren = get(figHandle, 'Children');
    formatterSCI_IpkBeta
end








