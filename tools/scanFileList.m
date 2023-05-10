HDEV_motorcad=MotorcadData(12);
HDEV_motorcad.motocadLabPath='Z:\01_Codes_Projects\git_Motor_System_Model\Mathworks_ref\HDEV_fluxmodel\HDEV_Model2\Lab'
HDEV_motorcad.proj_path=HDEV_motorcad.motorcadMotPath;
HDEV_motorcad.file_path=HDEV_motorcad.proj_path;
HDEV_motorcad.matfileFindList=what(HDEV_motorcad.motocadLabPath);
HDEV_motorcad.file_name='HDEV_Model2';
inputobj=HDEV_motorcad;

HDEV_motorcad.matfileFindList.mat
i=1

HDEVdata_Simulation=DataPkBetaMap(12);
HDEVdata_Simulation.MotorcadMat=load(HDEV_motorcad.matfileFindList.mat{i})
