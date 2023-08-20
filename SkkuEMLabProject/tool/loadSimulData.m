function opData=loadSimulData(mcad)
       
    
    %% WaveForm
    % Value
    % 파형
    TerminalLineToLine={'TerminalLineToLine12','TerminalLineToLine23','TerminalLineToLine34'};    
    for i=1:length(TerminalLineToLine)
        figure(1)
        opData.Wave.TerminalLineToLine=DoMotorCADEmagCalc(TerminalLineToLine{i}, mcad);
        hold on
    end
        legend(TerminalLineToLine, 'Location', 'Best');


    %% 기본파 전압 
    data=table2array(opData.Wave.TerminalLineToLine.dataTable(:,"GraphValue"))
    fftReal=fft(data)
    abs(fftReal(2))

    %% 상전압
    TerminalPhase={'TerminalVoltage1','TerminalVoltage2','TerminalVoltage3'};    
    for i=1:length(TerminalPhase)
        figure(2)
        opData.Wave.TerminalPhaseWave=DoMotorCADEmagCalc(TerminalPhase{i}, mcad);
        hold on
    end
        legend(TerminalPhase, 'Location', 'Best');
   %% 토크파형
    figure(3)
    opData.Wave.TorqueMSVWWave= DoMotorCADEmagCalc('TorqueMSVW', mcad)
    hold on
    % dqTorque= DoMotorCADEmagCalc('FluxLinkageTorqueTotal', mcad)
   

    %% 데이터
            % 선간전압
    [~,opData.PeakLineLineVoltageTerminal]=mcad.GetVariable('PeakLineLineVoltage');
    % [~,resultBasePoint.VfundLL]                      =mcad.GetVariable();
    % [~,resultBasePoint.Vfundphase]                   =mcad.GetVariable();

    
    % 입력전류 /위상각
    [~,opData.IPk]                           =mcad.GetVariable('PhaseCurrent');
    [~,opData.Irms]                          =mcad.GetVariable('RMSPhaseCurrent');
    [~,opData.PhaseAdvance]                  =mcad.GetVariable('LabOpPoint_PhaseAdvance');
    [~,opData.PhaseAdvance]                  =mcad.GetVariable('PhaseAdvance');
 
    % 전류밀도  
    [~,opData.Jpk]                             =mcad.GetVariable('PeakCurrentDensity');
    [~,opData.Jrms]                             =mcad.GetVariable('RMSCurrentDensity');
    opData.Irms/opData.Jrms;
    % [~,resultBasePoint.FEASlotArea]                             =mcad.GetVariable('FEASlotArea');
    % [~,resultBasePoint.GrossSlotFillFactor]                             =mcad.GetVariable('GrossSlotFillFactor');
        % resultBasePoint.FEASlotArea*resultBasePoint.GrossSlotFillFactor;


    % 역률
    % [~,resultBasePoint.WaveformPowerFactor]                            =mcad.GetVariable('WaveformPowerFactor');
    [~,opData.WaveformPowerFactor_THD]                            =mcad.GetVariable('WaveformPowerFactor_THD');
    [~,opData.PhasorPowerFactor]                            =mcad.GetVariable('PhasorPowerFactor');
    % [~,resultBasePoint.LabOpPoint_PowerFactor]                            =mcad.GetVariable('LabOpPoint_PowerFactor');
    
    % 평균토크 /리플
    [~,opData.ShaftTorque]                    =mcad.GetVariable('ShaftTorque');
    % [~,resultBasePoint.EMTorque]                       =mcad.GetVariable('AvTorqueMsVw');
    [~,opData.dqTorque]                       =mcad.GetVariable('AvTorqueDQ');
    
    [~,opData.TorqueRipple]                   =mcad.GetVariable('TorqueRippleMsVwPerCent (MsVw)');
    
    % 회전속도
    [opData.ShaftSpeed]                      =mcad.GetVariable('ShaftSpeed');

%% 손실 
[~,tempData.DCloss]                           =mcad.GetVariable('ConductorLoss');
[~,tempData.AClossMagneticMethod]                           =mcad.GetVariable('ACConductorLoss_MagneticMethod_Total');
% 철손 / 자석와류손;
[~,tempData.StatorIronLoss_Total]                          =mcad.GetVariable('StatorIronLoss_Total');
[~,tempData.RotorIronLoss_Total]                          =mcad.GetVariable('RotorIronLoss_Total');
[~,tempData.StatorBackIronLoss_Total]                          =mcad.GetVariable('StatorBackIronLoss_Total');
[~,tempData.StatorToothLoss_Total]                          =mcad.GetVariable('StatorToothLoss_Total');
 tempData.IronLossTotal=tempData.StatorIronLoss_Total+tempData.RotorIronLoss_Total;
% 자석손실
[~,tempData.Magloss]                           =mcad.GetVariable('MagnetLoss');
% 총손실
[~,tempData.TotalEMLoss]                      =mcad.GetVariable('Loss_Total');
% 효율
[~,tempData.Efficiency]                        =mcad.GetVariable('SystemEfficiency');

% 출력
% [~,tempData.Power.InputPower]                        =mcad.GetVariable('InputPower');
% [~,tempData.Power.ElectromagneticPower]                        =mcad.GetVariable('ElectromagneticPower');
[~,tempData.OutputPower]                                  =mcad.GetVariable('OutputPower');


%% Iron Loss
opData.PPT.IronLoss.kw.StatorBackIronLoss_Total=w2kw(tempData.StatorIronLoss_Total      );
opData.PPT.IronLoss.kw.StatorToothLoss_Total   =w2kw(tempData.RotorIronLoss_Total    );
opData.PPT.IronLoss.kw.StatorIronLoss_Total    =w2kw(tempData.StatorBackIronLoss_Total  );
opData.PPT.IronLoss.kw.RotorIronLoss_Total     =w2kw(tempData.StatorToothLoss_Total     );
opData.PPT.IronLoss.kw.IronLossTotal           =w2kw(tempData.IronLossTotal     );

opData.PPT.IronLoss.Ironpercent.StatorBackIronLoss_Total=percent(tempData.StatorBackIronLoss_Total/tempData.IronLossTotal)
opData.PPT.IronLoss.Ironpercent.StatorToothLoss_Total   =percent(tempData.StatorToothLoss_Total/tempData.IronLossTotal)
opData.PPT.IronLoss.Ironpercent.StatorIronLoss_Total    =percent(tempData.StatorIronLoss_Total/tempData.IronLossTotal)
opData.PPT.IronLoss.Ironpercent.RotorIronLoss_Total     =percent(tempData.RotorIronLoss_Total/tempData.IronLossTotal)

opData.PPT.IronLoss.TotalPercent.StatorBackIronLoss_Total=percent(tempData.StatorBackIronLoss_Total/tempData.TotalEMLoss)
opData.PPT.IronLoss.TotalPercent.StatorToothLoss_Total   =percent(tempData.StatorToothLoss_Total/tempData.TotalEMLoss)
opData.PPT.IronLoss.TotalPercent.StatorIronLoss_Total    =percent(tempData.StatorIronLoss_Total/tempData.TotalEMLoss)
opData.PPT.IronLoss.TotalPercent.RotorIronLoss_Total     =percent(tempData.RotorIronLoss_Total/tempData.TotalEMLoss)
opData.PPT.IronLoss.TotalPercent.IronLossTotal           =percent(tempData.IronLossTotal/tempData.TotalEMLoss)

%%

% tempData.kW.EMOutputDiffer=w2kw(tempData.IronLossTotal);
% tempData.kW.ElectromagneticPower-tempData.kW.MechanicallyLoss

opData.PPT.Loss.kw.DCloss             = w2kw(tempData.DCloss         )
opData.PPT.Loss.kw.AClossMagneticMethod  = w2kw(tempData.AClossMagneticMethod         )
opData.PPT.Loss.kw.IronLossTotal      = w2kw(tempData.IronLossTotal  )      
opData.PPT.Loss.kw.Magloss            = w2kw(tempData.Magloss        )  
opData.PPT.Loss.kw.TotalEMLoss        = w2kw(tempData.TotalEMLoss    )      
opData.PPT.Loss.OuputPower            =w2kw(tempData.OutputPower)

% Total Percent
opData.PPT.PercentLoss.Totalpercent.DCloss             = percent(tempData.DCloss       /tempData.TotalEMLoss  )
opData.PPT.PercentLoss.Totalpercent.AClossMagneticMethod             = percent(tempData.AClossMagneticMethod       /tempData.TotalEMLoss  )
opData.PPT.PercentLoss.Totalpercent.IronLossTotal      = percent(tempData.IronLossTotal/tempData.TotalEMLoss  )   
opData.PPT.PercentLoss.Totalpercent.Magloss            = percent(tempData.Magloss      /tempData.TotalEMLoss  )  
opData.PPT.PercentLoss.Totalpercent.TotalEMLoss        = percent(tempData.TotalEMLoss  /tempData.TotalEMLoss  )   

end

