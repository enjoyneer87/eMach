mcad=actxserver('motorcad.appautomation');

addpath(genpath(pwd))
%% 여기 변경해서 사용해주세요
fileDir='Z:\Simulation\LabProj2023BenchMarking\TeslaSPlaid';
fileName='S_Plaid_M_CAD_1335A_M270_35A.mot';

%% 진행
filePath=fullfile(fileDir,fileName);
mcad.LoadFromFile(filePath);

%% basePoint와 kw에 의한 결정
baserpm=5100;  % 이거에 의해 결정 
maxrpm=18000;
kW=380;
figure(6);
[baseTorque,MaxspeedTorque]=plotTNcurvebyBasePoint(baserpm, maxrpm, kW);
hold on

%% 차량에 의한 결정
MatFileData=plotEfficiencyMotorcad(matFilePath);

%% EMF

mcad.SetVariable('CoggingTorqueCalculation',1);
mcad.SetVariable('BackEMFCalculation',1);
% mcad.SetVariable('');
mcad.DoMagneticCalculation();

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

% cogging
[~,CoggingTorqueRippleVw]=mcad.GetVariable('CoggingTorqueRippleVw');

ResultStructEmagCalc=DoMotorCADEmagCalc('CoggingTorqueVW', mcad);

% 무부하 철손

% 동손/AC동손
[~,resultBasePoint.DCloss]                           =mcad.GetVariable('ConductorLoss');
[~,resultBasePoint.AClossMagneticMethod]                           =mcad.GetVariable('ACConductorLoss_MagneticMethod_Total');
% 철손 / 자석와류손;
[~,resultBasePoint.StatorIronLoss_Total]                          =mcad.GetVariable('StatorIronLoss_Total');
[~,resultBasePoint.RotorIronLoss_Total]                          =mcad.GetVariable('RotorIronLoss_Total');
resultBasePoint.IronLossTotal =resultBasePoint.StatorIronLoss_Total+resultBasePoint.RotorIronLoss_Total;
[~,resultBasePoint.Magloss]                           =mcad.GetVariable('MagnetLoss');


%% Load Point
% OP1 -Base
setOP2Emag(baserpm,baseTorque,mcad)

mcad.DoMagneticCalculation()




% Value
% 기본파 선간전압/ 상전압
[~,resultBasePoint.PeakLineLineVoltageTerminal]=mcad.GetVariable('PeakLineLineVoltage');
[~,resultBasePoint.VfundLL]                      =mcad.GetVariable();
[~,resultBasePoint.Vfundphase]                   =mcad.GetVariable();

% 파형
TerminalLineToLine={'TerminalLineToLine12','TerminalLineToLine23','TerminalLineToLine34'};    
for i=1:length(TerminalLineToLine)
    figure(3)
    ResultStructEmagCalcLine=DoMotorCADEmagCalc(TerminalLineToLine{i}, mcad);
    hold on
end
    legend(TerminalLineToLine, 'Location', 'Best');
fftReal=fft(data)
abs(fftReal(2))

data=table2array(ResultStructEmagCalcLine.dataTable(:,"GraphValue"))
TerminalPhase={'TerminalVoltage1','TerminalVoltage2','TerminalVoltage3'};    
for i=1:length(TerminalPhase)
    figure
    ResultStructEmagCalcPhase=DoMotorCADEmagCalc(TerminalPhase{i}, mcad)
    hold on
end
    legend(TerminalPhase, 'Location', 'Best');


% 전류밀도  
[~,resultBasePoint.Jpk]                             =mcad.GetVariable('PeakCurrentDensity');
[~,resultBasePoint.Jrms]                             =mcad.GetVariable('RMSCurrentDensity');
resultBasePoint.Irms/resultBasePoint.Jrms;
[~,resultBasePoint.FEASlotArea]                             =mcad.GetVariable('FEASlotArea');
[~,resultBasePoint.GrossSlotFillFactor]                             =mcad.GetVariable('GrossSlotFillFactor');

resultBasePoint.FEASlotArea*resultBasePoint.GrossSlotFillFactor;

% 입력전류 /위상각
[~,resultBasePoint.IPk]                           =mcad.GetVariable('PhaseCurrent');
[~,resultBasePoint.Irms]                          =mcad.GetVariable('RMSPhaseCurrent');
[~,resultBasePoint.PhaseAdvance]                  =mcad.GetVariable('LabOpPoint_PhaseAdvance');
[~,resultBasePoint.PhaseAdvance]                  =mcad.GetVariable('PhaseAdvance');


% 역률
[~,resultBasePoint.WaveformPowerFactor]                            =mcad.GetVariable('WaveformPowerFactor');
[~,resultBasePoint.WaveformPowerFactor_THD]                            =mcad.GetVariable('WaveformPowerFactor_THD');
[~,resultBasePoint.PhasorPowerFactor]                            =mcad.GetVariable('PhasorPowerFactor');
[~,resultBasePoint.LabOpPoint_PowerFactor]                            =mcad.GetVariable('LabOpPoint_PowerFactor');

% 평균토크 /리플
[~,resultBasePoint.ShaftTorque]                    =mcad.GetVariable('ShaftTorque');
[~,resultBasePoint.EMTorque]                       =mcad.GetVariable('AvTorqueMsVw');
[~,resultBasePoint.dqTorque]                       =mcad.GetVariable('AvTorqueDQ');

ResultStructEmagCalc= DoMotorCADEmagCalc('TorqueMSVW', mcad)
dqTorque= DoMotorCADEmagCalc('FluxLinkageTorqueTotal', mcad)

[~,resultBasePoint.TorqueRipple]                   =mcad.GetVariable('TorqueRippleMsVwPerCent (MsVw)');

% 회전속도
[resultBasePoint.ShaftSpeed]                      =baserpm;

% 동손/AC동손
[~,resultBasePoint.DCloss]                           =mcad.GetVariable('ConductorLoss');
[~,resultBasePoint.AClossMagneticMethod]                           =mcad.GetVariable('ACConductorLoss_MagneticMethod_Total');
% 철손 / 자석와류손;
[~,resultBasePoint.StatorIronLoss_Total]                          =mcad.GetVariable('StatorIronLoss_Total');
[~,resultBasePoint.RotorIronLoss_Total]                          =mcad.GetVariable('RotorIronLoss_Total');
[~,resultBasePoint.StatorBackIronLoss_Total]                          =mcad.GetVariable('StatorBackIronLoss_Total');
[~,resultBasePoint.StatorToothLoss_Total]                          =mcad.GetVariable('StatorToothLoss_Total');


w2kw(resultBasePoint.StatorToothLoss_Total)

%% PPT 기입부
PPT.IronLoss.kw.StatorBackIronLoss_Total=w2kw(resultBasePoint.StatorIronLoss_Total      );
PPT.IronLoss.kw.StatorToothLoss_Total   =w2kw(resultBasePoint.RotorIronLoss_Total    );
PPT.IronLoss.kw.StatorIronLoss_Total    =w2kw(resultBasePoint.StatorBackIronLoss_Total  );
PPT.IronLoss.kw.RotorIronLoss_Total     =w2kw(resultBasePoint.StatorToothLoss_Total     );
PPT.IronLoss.kw.IronLossTotal           =w2kw(resultBasePoint.IronLossTotal     );


PPT.IronLoss.Ironpercent.StatorBackIronLoss_Total=percent(resultBasePoint.StatorBackIronLoss_Total/resultBasePoint.IronLossTotal)
PPT.IronLoss.Ironpercent.StatorToothLoss_Total   =percent(resultBasePoint.StatorToothLoss_Total/resultBasePoint.IronLossTotal)
PPT.IronLoss.Ironpercent.StatorIronLoss_Total    =percent(resultBasePoint.StatorIronLoss_Total/resultBasePoint.IronLossTotal)
PPT.IronLoss.Ironpercent.RotorIronLoss_Total     =percent(resultBasePoint.RotorIronLoss_Total/resultBasePoint.IronLossTotal)

PPT.IronLoss.TotalPercent.StatorBackIronLoss_Total=percent(resultBasePoint.StatorBackIronLoss_Total/resultBasePoint.TotalEMLoss)
PPT.IronLoss.TotalPercent.StatorToothLoss_Total   =percent(resultBasePoint.StatorToothLoss_Total/resultBasePoint.TotalEMLoss)
PPT.IronLoss.TotalPercent.StatorIronLoss_Total    =percent(resultBasePoint.StatorIronLoss_Total/resultBasePoint.TotalEMLoss)
PPT.IronLoss.TotalPercent.RotorIronLoss_Total     =percent(resultBasePoint.RotorIronLoss_Total/resultBasePoint.TotalEMLoss)
PPT.IronLoss.TotalPercent.IronLossTotal           =percent(resultBasePoint.IronLossTotal/resultBasePoint.TotalEMLoss)




w2kw(resultBasePoint.StatorBackIronLoss_Total) 
resultBasePoint.IronLossTotal =resultBasePoint.StatorIronLoss_Total+resultBasePoint.RotorIronLoss_Total;
[~,resultBasePoint.Magloss]                           =mcad.GetVariable('MagnetLoss');
w2kw(resultBasePoint.IronLossTotal)


% 총손실
[~,resultBasePoint.TotalEMLoss]                      =mcad.GetVariable('Loss_Total');

% 효율
[~,resultBasePoint.Efficiency]                        =mcad.GetVariable('SystemEfficiency');
 resultBasePoint.OutputPower/(resultBasePoint.OutputPower+resultBasePoint.TotalEMLoss)*100

% 출력

[~,resultBasePoint.Power.InputPower]                        =mcad.GetVariable('InputPower');
[~,resultBasePoint.Power.ElectromagneticPower]                        =mcad.GetVariable('ElectromagneticPower');
[~,resultBasePoint.Power.OutputPower]                                  =mcad.GetVariable('OutputPower');
rpm2radsec(resultBasePoint.ShaftSpeed)*resultBasePoint.ShaftTorque/1000; % OutputPower = Shaft Torque*rpm

[~,resultBasePoint.Efficiency]                                  =mcad.GetVariable('SystemEfficiency');

%%kW

resultBasePoint.kW.InputPower               =w2kw(resultBasePoint.Power.InputPower)
resultBasePoint.kW.ElectromagneticPower     =w2kw(resultBasePoint.Power.ElectromagneticPower)
resultBasePoint.kW.OutputPower              =w2kw(resultBasePoint.Power.OutputPower)

resultBasePoint.kW.InputPower-resultBasePoint.kW.ElectromagneticPower    % 입력 - 전자계출력
% Hybrid AC동손
w2kw(resultBasePoint.DCloss+resultBasePoint.AClossMagneticMethod+resultBasePoint.Magloss) %  동손+AC동손+자석와류손
% Full FEA
w2kw(resultBasePoint.TotalEMLoss-resultBasePoint.IronLossTotal)          % 총손실 - 철손

w2kw(resultBasePoint.StatorIronLoss_Total)
w2kw(resultBasePoint.RotorIronLoss_Total)

resultBasePoint.kW.EMOutputDiffer=w2kw(resultBasePoint.IronLossTotal);
resultBasePoint.kW.ElectromagneticPower-resultBasePoint.kW.MechanicallyLoss
resultBasePoint.kW.TotalEMLoss=resultBasePoint.TotalEMLoss/1000;


% Loss Ratio  
resultBasePoint.DCloss/resultBasePoint.TotalEMLoss
resultBasePoint.ACloss/resultBasePoint.TotalEMLoss*100
resultBasePoint.IronLossTotal/resultBasePoint.TotalEMLoss*100




resultBasePoint.Magloss/resultBasePoint.TotalEMLoss*100

resultBasePoint.DCloss/resultBasePoint.OutputPower*100
resultBasePoint.ACloss/resultBasePoint.OutputPower*100
resultBasePoint.IronLossTotal/resultBasePoint.OutputPower*100
resultBasePoint.Magloss/resultBasePoint.OutputPower*100


resultBasePoint.DCloss/resultBasePoint.ElectromagneticPower*100
resultBasePoint.ACloss/resultBasePoint.ElectromagneticPower*100
resultBasePoint.IronLossTotal/resultBasePoint.ElectromagneticPower*100
resultBasePoint.Magloss/resultBasePoint.ElectromagneticPower*100


% OP2 -Maximum
setOP2Emag(maxrpm,MaxspeedTorque,mcad)
mcad.DoMagneticCalculation()


%% Load Effimap
JH

%% Plot Each Contour
FEAscreenName='E-Magnetics;FEA';
screenFEA=strsplit(FEAscreenName,';');

% FEAscreenFileName=fullfile(fileDir,[screenFEA{2},'.png']);
mcad.DisplayScreen(FEAscreenName)
mcad.SetVariable('FEShading_Magnetic',1)
mcad.InitialiseTabNames()
mcad.SaveMotorCADScreenToFile(FEAscreenName,"Z:\fea.png")


