%% 입력

MatFileDir='Z:\Simulation\LabProj2023BenchMarking\TeslaSPlaid\S_Plaid_M_CAD_1335A_LossModelLSC\Lab'
MatFilename='MotorLAB_elecdata.mat'
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
calcVehicleLateralDynamics(0,vehicleData,vehiclePerformData,[2/4 1/4 1/4]);                %[TC] 변수 변경필요
