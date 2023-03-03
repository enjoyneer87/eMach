%% object make
HDEV_motorcad=MotorcadData(12);
HDEVdata=DataPkBetaMap(HDEV_motorcad.p);
PmsmFem.NumPolePairs = HDEVdata.p/2;


HDEV_motorcad.motorcadMotPath='Z:\Thesis\Optislang_Motorcad\Validation'
HDEV_motorcad.motocadLabPath=strcat('Z:\01_Codes_Projects\git_Motor_System_Model\Mathworks_ref\HDEV_fluxmodel\HDEV_Model2','\Lab\');
HDEV_motorcad.proj_path=HDEV_motorcad.motorcadMotPath;
HDEV_motorcad.file_path=HDEV_motorcad.proj_path;

HDEV_motorcad.matfileFindList=what(HDEV_motorcad.motocadLabPath);

HDEV_motorcad.file_name='HDEV_Model2';
inputobj=HDEV_motorcad;
%% Raw PsiDModel_Lab import(should do manually) - ModelParameters_MotorLAB- 
HDEV_motorcad.ModelParameters_MotorLAB
inputobj=inputobj.rawPsiDataPost() %manual

%%
%%currentVec
NcurrentVec=5
currentMax=1000;
currentVec=[0:currentMax/(NcurrentVec):currentMax]'
phaseMax=90;
NphaseVec=5
phaseVec=[0:phaseMax/(NphaseVec-1):phaseMax];

HDEVdata.phaseVec=phaseVec;
HDEVdata.currentVec=currentVec;
HDEV_motorcad=inputobj;
%% mesh for Psi data
currentmesh = repmat(HDEVdata.currentVec,1,length(phaseVec))
size(currentmesh)
phasemesh = repmat(HDEVdata.phaseVec,length(currentmesh),1)
size(phasemesh)

%% plot Psi point Lab 
subplot(1,2,1)
% surf(HDEVdata.phaseVec,HDEVdata.currentVec,HDEV_motorcad.ModelParameters_MotorLAB.PsiDModel_Lab)

scatter3(phasemesh,currentmesh,HDEV_motorcad.ModelParameters_MotorLAB.PsiDModel_Lab,'blue')
hold on
subplot(1,2,2)
% surf(HDEVdata.phaseVec,HDEVdata.currentVec,HDEV_motorcad.ModelParameters_MotorLAB.PsiQModel_Lab)
scatter3(phasemesh,currentmesh,HDEV_motorcad.ModelParameters_MotorLAB.PsiQModel_Lab,'blue')
hold on

%% LabMat Import - ref compMatFile
HDEV_motorcad.proj_path=HDEV_motorcad.motorcadMotPath;
HDEV_motorcad.file_path=HDEV_motorcad.proj_path;

HDEV_motorcad.motocadLabPath=strcat('Z:\01_Codes_Projects\git_Motor_System_Model\Mathworks_ref\HDEV_fluxmodel\HDEV_Model2','\Lab\');
HDEV_motorcad.matfileFindList=what(HDEV_motorcad.motocadLabPath);

% mcad = actxserver('MotorCAD.AppAutomation');
HDEV_motorcad.matfileFindList.mat
i=2
HDEVdata.MotorcadMat=load(HDEV_motorcad.matfileFindList.mat{i})
dataobj=HDEVdata

%% Plot Mat flux from Saturation (High Fidel)
dataobj=HDEVdata.compMatiFilePsi()

figHandles = findobj('Type', 'figure');

% 각 figure의 모든 subfigure 객체 호출
for i = 1:length(figHandles)
    figHandle = figHandles(i);
    figChildren = get(figHandle, 'Children');
    formatterSCI_IpkBeta
end








