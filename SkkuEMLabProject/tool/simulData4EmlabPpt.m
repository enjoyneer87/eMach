mcad=actxserver('motorcad.appautomation');

%% 여기 변경해서 사용해주세요
fileDir='Z:\Simulation\LabProj2023BenchMarking\TeslaSPlaid'
fileName='S_Plaid_M_CAD_1335A_LossModelLSC.mot'

%% 진행
filePath=fullfile(fileDir,fileName)
mcad.LoadFromFile(filePath);

%% basePoint와 kw에 의한 결정
baserpm=5100  % 이거에 의해 결정 
maxrpm=18000
kW=380
figure(1)
[baseTorque,MaxspeedTorque]=plotTNcurvebyBasePoint(baserpm, maxrpm, kW);
hold on

%% 차량에 의한 결정
MatFileData=plotEfficiencyMotorcad(matFilePath);

%% EMF

mcad.SetVariable('CoggingTorqueCalculation',1)
mcad.SetVariable('BackEMFCalculation',1)
mcad.SetVariable('')
mcad.DoMagneticCalculation()

PhEMF={'BackEMFPh1',   'BackEMFPh2','BackEMFPh3'}          ;
LLEMF={'BackEMFLineToLine12','BackEMFLineToLine23','BackEMFLineToLine34'}    ;

for i = 1:length(PhEMF)
    figure(1)
    plotBEMFMotorCAD(PhEMF{i}, mcad);
    hold on; % Hold on to overlay plots
end
    legend(PhEMF, 'Location', 'Best');

for i = 1:length(LLEMF)
   figure(2)
    plotBEMFMotorCAD(LLEMF{i},mcad)
    hold on
end
    legend(LLEMF, 'Location', 'Best');

[~,BEMFLLpk]=mcad.GetVariable('PeakBackEMFLine');
[~,BEMFLLrms]=mcad.GetVariable('RMSBackEMFLine');

[~,BEMFphpk]=mcad.GetVariable('PeakBackEMFPhase');
[~,BEMFTHD]=mcad.GetVariable('THDBackEMFLine');


%% Load Point
% OP1 -Base
setOP2Emag(baserpm,baseTorque,mcad)
plotMagenticGraph(,mcad)

mcad.DoMagneticCalculation()

% OP2 -Maximum


%% Load Effimap


%% Plot Each Contour



