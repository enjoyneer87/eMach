%% 입력

MatFileDir='Z:\Simulation\LabProj2023v2\6p54V\DOE\6p54s_V_Vacodur49_Design0300\6p54s_V_Vacodur49_Design0300\Lab'
MatFilename='MotorLAB_elecdata_12h18m.mat'
gitpath='Z:\01_Codes_Projects\git_fork_emach\'


%% 실행
addpath(genpath(MatFileDir));
matFilePath=fullfile(MatFileDir,MatFilename)
% matFil
addpath(genpath(pwd))

addpath(genpath(gitpath))
vehicleData=load("TeslaSPlaid.mat");                             % TeslaPlaid Define
vehicleData=vehicleData.TeslaPlaid;
vehicleData.N_d_MotorLAB=7.56;  %[TC] 범용성 증가 필요

% vehiclePowerCurve=load("TeslaSPlaidPowerCurveDigitizer.mat");   % TeslaPowerCurve Define
% vehiclePowerCurve=vehiclePowerCurve.TeslaPowerCurve;
% vehiclePerformData          = calcVehiclePerformance(vehiclePowerCurve);   %vehiclePerformData define
TeslaPlaidCurve

figure(6)
MatFileData=plotEfficiencyMotorcad(matFilePath);
calcVehicleLateralDynamics(0,vehicleData,vehiclePerformData,[1/3 1/3 1/3]);                %[TC] 변수 변경필요
