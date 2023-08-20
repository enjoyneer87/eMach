function NoloadSimul=noloadSimulData(mcad)
mcad.SetVariable('CoggingTorqueCalculation',1);
mcad.SetVariable('BackEMFCalculation',1);
% mcad.SetVariable('');
% mcad.DoMagneticCalculation();

PhEMF={'BackEMFPh1',   'BackEMFPh2','BackEMFPh3'}          ;

for i = 1:length(PhEMF)
    figure(1)
    NoloadSimul.EMFwave.phase=plotBEMFMotorCAD(PhEMF{i}, mcad);
    hold on; % Hold on to overlay plots
end
    legend(PhEMF, 'Location', 'Best');


    LLEMF={'BackEMFLineToLine12','BackEMFLineToLine23','BackEMFLineToLine34'}    ;

for i = 1:length(LLEMF)
   figure(2)
     NoloadSimul.EMFwave.Line=plotBEMFMotorCAD(LLEMF{i},mcad)
    hold on
end
    legend(LLEMF, 'Location', 'Best');

[~,NoloadSimul.BEMFLLpk]=mcad.GetVariable('PeakBackEMFLine');
[~,NoloadSimul.BEMFLLrms]=mcad.GetVariable('RMSBackEMFLine');
[~,NoloadSimul.BEMFphpk]=mcad.GetVariable('PeakBackEMFPhase');
[~,NoloadSimul.BEMFTHD]=mcad.GetVariable('THDBackEMFLine');

% cogging
[~,NoloadSimul.Cogging.CoggingTorqueRippleVw]=mcad.GetVariable('CoggingTorqueRippleVw');
figure(3)
NoloadSimul.Cogging.waveform=plotMotorCADCoggingCalc('CoggingTorqueVW', mcad);

% 무부하 철손

% 동손/AC동손
[~,NoloadSimul.DCloss]                           =mcad.GetVariable('ConductorLoss');
[~,NoloadSimul.AClossMagneticMethod]                           =mcad.GetVariable('ACConductorLoss_MagneticMethod_Total');
% 철손 / 자석와류손;
[~,NoloadSimul.StatorIronLoss_Total]                          =mcad.GetVariable('StatorIronLoss_Total');
[~,NoloadSimul.RotorIronLoss_Total]                          =mcad.GetVariable('RotorIronLoss_Total');
NoloadSimul.IronLossTotal =NoloadSimul.StatorIronLoss_Total+NoloadSimul.RotorIronLoss_Total;
[~,NoloadSimul.Magloss]                           =mcad.GetVariable('MagnetLoss');

end