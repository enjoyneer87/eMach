function resultBasePoint=getMCADEmagResult(mcad)
% 계산한거는 뒤에 sum
% 뽑은거는 앞이나 뒤에  totalR
% 전류밀도  
[~,resultBasePoint.Jpk]                          =mcad.GetVariable('PeakCurrentDensity');
[~,resultBasePoint.Jrms]                         =mcad.GetVariable('RMSCurrentDensity');
[~,resultBasePoint.FEASlotArea]                  =mcad.GetVariable('FEASlotArea');
[~,resultBasePoint.GrossSlotFillFactor]          =mcad.GetVariable('GrossSlotFillFactor');
% 입력전류 /위상각
[~,resultBasePoint.IPk]                           =mcad.GetVariable('PhaseCurrent');
[~,resultBasePoint.Irms]                          =mcad.GetVariable('RMSPhaseCurrent');
[~,resultBasePoint.PhaseAdvance]                  =mcad.GetVariable('LabOpPoint_PhaseAdvance');
[~,resultBasePoint.PhaseAdvance]                  =mcad.GetVariable('PhaseAdvance');
% 전압 
[~,resultBasePoint.PhaseVoltage]                  =mcad.GetVariable('PhaseVoltage');
[~,resultBasePoint.LineLineVoltage]                          =mcad.GetVariable('LineLineVoltage');
[~,resultBasePoint.VoltageConversionFactor]                          =mcad.GetVariable('VoltageConversionFactor');
resultBasePoint.Irms/resultBasePoint.Jrms


% 역률
[~,resultBasePoint.WaveformPowerFactor]                            =mcad.GetVariable('WaveformPowerFactor');
[~,resultBasePoint.WaveformPowerFactor_THD]                            =mcad.GetVariable('WaveformPowerFactor_THD');
[~,resultBasePoint.PhasorPowerFactor]                            =mcad.GetVariable('PhasorPowerFactor');
[~,resultBasePoint.LabOpPoint_PowerFactor]                            =mcad.GetVariable('LabOpPoint_PowerFactor');
% 회전속도
[~,resultBasePoint.ShaftSpeed]                      =mcad.GetVariable('ShaftSpeed');
[~,resultBasePoint.ConductorLoss                ]                                    = mcad.GetVariable("ConductorLoss")
[~,resultBasePoint.DCConductorLoss_Armature_A   ]                                    = mcad.GetVariable("DCConductorLoss_Armature_A")
[~,resultBasePoint.ACConductorLoss_MagneticMethod_Total  ]                           = mcad.GetVariable("ACConductorLoss_MagneticMethod_Total")

% [~,resultBasePoint.AClossMagneticMethod]             =mcad.GetVariable('ACConductorLoss_MagneticMethod_Total');
% 철손 / 자석와류손;
[~,resultBasePoint.StatorIronLoss_Total]             =mcad.GetVariable('StatorIronLoss_Total');
[~,resultBasePoint.RotorIronLoss_Total]              =mcad.GetVariable('RotorIronLoss_Total');
[~,resultBasePoint.StatorBackIronLoss_Total]         =mcad.GetVariable('StatorBackIronLoss_Total');
[~,resultBasePoint.StatorToothLoss_Total]            =mcad.GetVariable('StatorToothLoss_Total');
% 평균토크 /리플
[~,resultBasePoint.ShaftTorque]                    =mcad.GetVariable('ShaftTorque');
[~,resultBasePoint.EMTorque]                       =mcad.GetVariable('AvTorqueMsVw');
[~,resultBasePoint.dqTorque]                       =mcad.GetVariable('AvTorqueDQ');
%
[~,resultBasePoint.Magnetloss]                     =mcad.GetVariable('MagnetLoss');

% % ConductorLoss
% 자석손실
[~,resultBasePoint.Magnetloss]                     =mcad.GetVariable('MagnetLoss');
% 총손실
[~,resultBasePoint.TotalEMLoss]                      =mcad.GetVariable('Loss_Total');

%Check
% 출력
[~,resultBasePoint.Power.InputPower]                        =mcad.GetVariable('InputPower');             % OutputPower+TotalEMLoss
[~,resultBasePoint.Power.ElectromagneticPower]              =mcad.GetVariable('ElectromagneticPower');   % ElectromagneticPower =Electromagnetic torque * rpm
[~,resultBasePoint.Power.OutputPower]                       =mcad.GetVariable('OutputPower');            % OutputPower = Shaft Torque*rpm 
% 효율
[~,resultBasePoint.SystemEfficiency]                         =mcad.GetVariable('SystemEfficiency');

resultBasePoint.Power.InputPower-resultBasePoint.Power.OutputPower-resultBasePoint.TotalEMLoss

end