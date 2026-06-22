%[text:tableOfContents]{"heading":"목차"}

McadWattsTable=getMCADWattsTable(mcad)
McadWattsTable = filterMCADTableZeroValue(McadWattsTable)
% filterMCADAutomationNameTable
powerTable=filterMCADTable(McadWattsTable,'Power')
IronLossTable=filterMCADTable(McadWattsTable,'Iron')

% 계산한거는 뒤에 sum
% 뽑은거는 앞이나 뒤에  total
% 전류밀도  
[~,resultBasePoint.Jpk]                              =mcad.GetVariable('PeakCurrentDensity');
[~,resultBasePoint.Jrms]                             =mcad.GetVariable('RMSCurrentDensity');
resultBasePoint.Irms/resultBasePoint.Jrms;
[~,resultBasePoint.FEASlotArea]                      =mcad.GetVariable('FEASlotArea');
[~,resultBasePoint.GrossSlotFillFactor]              =mcad.GetVariable('GrossSlotFillFactor');
% 입력전류 /위상각
[~,resultBasePoint.IPk]                           =mcad.GetVariable('PhaseCurrent');
[~,resultBasePoint.Irms]                          =mcad.GetVariable('RMSPhaseCurrent');
[~,resultBasePoint.PhaseAdvance]                  =mcad.GetVariable('LabOpPoint_PhaseAdvance');
[~,resultBasePoint.PhaseAdvance]                  =mcad.GetVariable('PhaseAdvance');
% 전압 
[~,resultBasePoint.PhaseVoltage]                          =mcad.GetVariable('PhaseVoltage');
[~,resultBasePoint.LineLineVoltage]                          =mcad.GetVariable('LineLineVoltage');
[~,resultBasePoint.VoltageConversionFactor]                          =mcad.GetVariable('VoltageConversionFactor');


% 역률
[~,resultBasePoint.WaveformPowerFactor]                            =mcad.GetVariable('WaveformPowerFactor');
[~,resultBasePoint.WaveformPowerFactor_THD]                            =mcad.GetVariable('WaveformPowerFactor_THD');
[~,resultBasePoint.PhasorPowerFactor]                            =mcad.GetVariable('PhasorPowerFactor');
[~,resultBasePoint.LabOpPoint_PowerFactor]                            =mcad.GetVariable('LabOpPoint_PowerFactor');
% 회전속도
[~,resultBasePoint.ShaftSpeed]                      =mcad.GetVariable('ShaftSpeed');
%%
%[text] %[text:anchor:H_A28C22F9] ## 손실
[~,resultBasePoint.ConductorLoss                ]                           = mcad.GetVariable("ConductorLoss")
[~,resultBasePoint.DCConductorLoss_Armature_A   ]                                    = mcad.GetVariable("DCConductorLoss_Armature_A")
[~,resultBasePoint.ACConductorLoss_MagneticMethod_Total  ]                                   = mcad.GetVariable("ACConductorLoss_MagneticMethod_Total")

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
[~,resultBasePoint.Magnetloss]                           =mcad.GetVariable('MagnetLoss');

ConductorLoss
% 자석손실
[~,resultBasePoint.Magnetloss]                           =mcad.GetVariable('MagnetLoss');
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

%%
%[text] %[text:anchor:H_B89764FA] ## 손실 Table 데이터
%[text] 
%[text] Mechanical : Iron Loss, MagnetLoss,  AC winding loss
%[text] 1\. J. Goss, P. H. Mellor, R.  Wrobel, D. A. Staton, and M. Popescu, “The design of AC permanent magnet motors  for electric vehicles: a computationally efficient model of the operational  envelope,” in *6th IET International  Conference on Power Electronics, Machines and Drives (PEMD 2012)*, 2012, pp. B21–B21. 
%[text] 
%[text] 2\. P. H. Mellor, R. Wrobel, and  D. Holliday. A computationally efficient iron loss model for brushless ac  machines that caters for rated flux and field weakened operation. In  *Proc.  IEEE Int. Electric Machines and Drives Conf. IEMDC ’09*, pages 490–494, 2009.
%[text] **Lab Model**
%[text] 
%[text] **Iron Losses** are treated **mechanically** and subtracted from the electromagnetic output  power and torque to calculate the shaft output power and torque.
%[text] 
%[text] **Magnet Losses** are treated **mechanically** and subtracted from the electromagnetic output  power and torque to calculate the shaft output power and torque.
%[text] 
%[text] The **AC winding loss** component **due to magnet excitation** is treated **mechanically**. This is  found by performing a transient FEA simulation with zero stator current and  calculating the AC winding losses. Since this component does not depend on  **stator current/magnitude** or temperature, it is scaled only with speed as:
%[text] $&dollar&;W\_{\\text {eale }}=W\_{\\text {ref }}\\left(\\frac{n\_{\\text {eale }}}{n\_{\\text {ref }}}\\right)^\\zeta&dollar&;$
%[text] The component due to **stator winding excitatio**n is treated **electrically**. FEA  calculations are undertaken to calculate the variation of the AC winding loss  with stator current magnitude/angle and rotor current (depending on machine  type). The loss at each point is then calculated by interpolating between model  build points and scaling with frequency/temperature. After interpolation, **the  magnet excitation component (if present) is subtracted from each to find the  stator winding excitation component**. This component is then scaled with speed  and temperature by:
%[text] $&dollar&;W\_{\\text {cale }}=\\frac{W\_{\\text {ref }} \\cdot\\left(\\frac{n\_{\\text {calc }}}{n\_{\\text {ref }}}\\right)^\\zeta}{\\left(\\frac{1+\\alpha\\left(T\_{\\text {calc }}-20\\right)}{1+\\alpha\\left(T\_{\\text {ref }}-20\\right)}\\right)^\\beta}&dollar&;$
%[text] 
%[text] 
checkdefEmagEff_MCADHybridNFullFEAi
McadWattsTable=defMCADWattsTable()
% defMCADMagneticTable

% McadWattsTable = filterMCADTableZeroValue(McadWattsTable)
% McadWattsTable = convertMcadTable2UnvTable(McadWattsTable)

% Joule
ConductorLossTable=filterMCADTable(McadWattsTable,'conductor')
ConductorLossTable = convertMCADTableCurrentValueToDouble(ConductorLossTable)
% Iron
statorLossTable=filterMCADTable(McadWattsTable,'stator')
rotorLossTable=filterMCADTable(McadWattsTable,'rotor')
statorLossTable = convertMCADTableCurrentValueToDouble(statorLossTable)
rotorLossTable  = convertMCADTableCurrentValueToDouble(rotorLossTable)
TotalStatorLossTable=filterMCADTable(statorLossTable,'total')
TotalRotorLossTable=filterMCADTable(rotorLossTable,'total')

% Magnet
MagnetLossTable = filterMCADTable(McadWattsTable,'MagnetLoss')
MagnetLossTable = convertMCADTableCurrentValueToDouble(MagnetLossTable)

% Mag Table
McadMagTable = defMCADMagneticTable()
McadMagTable = convertMcadTable2UnvTable(McadMagTable)

% Power
powerTable  = filterMCADTable(McadMagTable,'Power')
powerTable  = convertMCADTableCurrentValueToDouble(powerTable)

% Torque

torqueTable = filterMCADTable(McadMagTable,'torque')
torqueTable = filterMCADTableWithAnyInfo(torqueTable,'Nm','Units')
torqueTable = getMcadTableVariable(torqueTable,mcad)
torqueTable = convertMCADTableCurrentValueToDouble(torqueTable)
torqueTable = filterMCADTableZeroValue(torqueTable)

%% 전압
voltageTable = filterMCADTableWithAnyInfo(McadMagTable,'volts','Units')
voltageTable = getMcadTableVariable(voltageTable,mcad)
voltageTable = convertMCADTableCurrentValueToDouble(voltageTable)
voltageTable = filterMCADTableZeroValue(voltageTable)

%%
%[text] %[text:anchor:H_DC095B29] ## 편한 데이터
voltageStrct = MCADtable2Struct(voltageTable)
torqueStrcut = MCADtable2Struct(torqueTable)
powerStrct = MCADtable2Struct(powerTable)

stLossStruct = MCADtable2Struct(statorLossTable)
rtLossStr = MCADtable2Struct(rotorLossTable)
ConductorStrcut = MCADtable2Struct(ConductorLossTable)
MagnetLossStrcut = MCADtable2Struct(MagnetLossTable)

MagnetLossStrcut.MagnetLoss_Adj

isSimiliar   = difftol(voltageStrct.LineLineVoltage,voltageStrct.DCBusVoltage/sqrt(2),1e-4)


%%
%[text] %[text:anchor:H_2E01D9BF] ## 
%%
%[text] %[text:anchor:H_D931C469] ## kW
FinalLossList={
'ConductorLoss',
'ACConductorLoss_MagneticMethod_Total',
'StatorIronLoss_Total_Adj',
'RotorIronLoss_Total_Adj',
'MagnetLoss_Adj',
'Loss_[Windage]'};

%%\
McadFinalLossWattsTable=filterMCADTable(McadWattsTable,FinalLossList,'exact')
McadFinalLossWattsTable=getMcadTableVariable(McadFinalLossWattsTable,mcad)
McadFinalLossWattsTable = convertMCADTableCurrentValueToDouble(McadFinalLossWattsTable)
McadFinalLossWattsTable = filterMCADTableZeroValue(McadFinalLossWattsTable)
McadFinalLossWattsTable = convertMcadTable2UnvTable(McadFinalLossWattsTable)
totalLoss=sum(McadFinalLossWattsTable.doubleValue)
%
FullFEAOCMcadWattsTable=getMCADWattsTable(mcad)
FullFEAOCMcadWattsTable
FullFEALossStrcut = MCADtable2Struct(FullFEAOCMcadWattsTable)
FullFEALossStrcut.ACConductorLoss_MagneticMethod_Total
FullFEALossStrcut.ConductorLoss
FullFEALossStrcut.DCConductorLoss_Armature_A
%%% Magnet FEA Loss
McadOCLossWattsTable=getFindMcadUnvTable(mcad,'OC',McadWattsTable)

% OC

% Mechanically


(totalLoss-Loss_Total)/1000
PhasorInputkW=3*(ResultMotorcadEmagPhasorDiagram.PhasorRMSPhaseVoltage*ResultMotorcadEmagPhasorDiagram.RMSPhaseCurrent)/1000

%[text] %[text:anchor:H_0E5C27D8] ## PPT 기입부
% Power
resultBasePoint.IronLossSum =resultBasePoint.StatorIronLoss_Total+resultBasePoint.RotorIronLoss_Total;


w2kw(resultBasePoint.StatorToothLoss_Total)


resultBasePoint.Power.EMPower5EMTorque=rpm2radsec(resultBasePoint.ShaftSpeed)*resultBasePoint.EMTorque/1000
rpm2radsec(resultBasePoint.ShaftSpeed)*resultBasePoint.ShaftTorque/1000;                                 % OutputPower = Shaft Torque*rpm
tempEffi= resultBasePoint.Power.OutputPower/(resultBasePoint.Power.OutputPower+resultBasePoint.TotalEMLoss)*100

resultBasePoint.FEASlotArea*resultBasePoint.GrossSlotFillFactor;

% 철손
PPT.IronLoss.kw.StatorBackIronLoss_Total=w2kw(resultBasePoint.StatorIronLoss_Total      );
PPT.IronLoss.kw.StatorToothLoss_Total   =w2kw(resultBasePoint.RotorIronLoss_Total    );
PPT.IronLoss.kw.StatorIronLoss_Total    =w2kw(resultBasePoint.StatorBackIronLoss_Total  );
PPT.IronLoss.kw.RotorIronLoss_Total     =w2kw(resultBasePoint.StatorToothLoss_Total     );
PPT.IronLoss.kw.IronLossSum             =w2kw(resultBasePoint.IronLossTotal     );
PPT.IronLoss.Ironpercent.StatorBackIronLoss_Total=percent(resultBasePoint.StatorBackIronLoss_Total/resultBasePoint.IronLossSum)
PPT.IronLoss.Ironpercent.StatorToothLoss_Total   =percent(resultBasePoint.StatorToothLoss_Total/resultBasePoint.IronLossSum)
PPT.IronLoss.Ironpercent.StatorIronLoss_Total    =percent(resultBasePoint.StatorIronLoss_Total/resultBasePoint.IronLossSum)
PPT.IronLoss.Ironpercent.RotorIronLoss_Total     =percent(resultBasePoint.RotorIronLoss_Total/resultBasePoint.IronLossSum)

PPT.IronLoss.TotalPercent.StatorBackIronLoss_Total=percent(resultBasePoint.StatorBackIronLoss_Total/resultBasePoint.TotalEMLoss)
PPT.IronLoss.TotalPercent.StatorToothLoss_Total   =percent(resultBasePoint.StatorToothLoss_Total/resultBasePoint.TotalEMLoss)
PPT.IronLoss.TotalPercent.StatorIronLoss_Total    =percent(resultBasePoint.StatorIronLoss_Total/resultBasePoint.TotalEMLoss)
PPT.IronLoss.TotalPercent.RotorIronLoss_Total     =percent(resultBasePoint.RotorIronLoss_Total/resultBasePoint.TotalEMLoss)
PPT.IronLoss.TotalPercent.IronLossSum           =percent(resultBasePoint.IronLossSum/resultBasePoint.TotalEMLoss)

w2kw(resultBasePoint.StatorBackIronLoss_Total) 
resultBasePoint.IronLossTotal =resultBasePoint.StatorIronLoss_Total+resultBasePoint.RotorIronLoss_Total;
w2kw(resultBasePoint.IronLossSum)

resultBasePoint.kW.InputPower               =w2kw(resultBasePoint.Power.InputPower)
resultBasePoint.kW.ElectromagneticPower     =w2kw(resultBasePoint.Power.ElectromagneticPower)
resultBasePoint.kW.OutputPower              =w2kw(resultBasePoint.Power.OutputPower)

resultBasePoint.kW.InputPower-resultBasePoint.kW.ElectromagneticPower    % 입력 - 전자계출력
% Hybrid AC동손
w2kw(resultBasePoint.DCloss+resultBasePoint.AClossMagneticMethod+resultBasePoint.Magnetloss) %  동손+AC동손+자석와류손
% Full FEA
w2kw(resultBasePoint.TotalEMLoss-resultBasePoint.IronLossTotal)          % 총손실 - 철손

w2kw(resultBasePoint.StatorIronLoss_Total)
w2kw(resultBasePoint.RotorIronLoss_Total)

resultBasePoint.kW.EMOutputDiffer=w2kw(resultBasePoint.IronLossTotal);
resultBasePoint.kW.ElectromagneticPower-resultBasePoint.kW.MechanicallyLoss
resultBasePoint.kW.TotalEMLoss=resultBasePoint.TotalEMLoss/1000;

%%\
PPT.Loss.DCloss             = w2kw(resultBasePoint.DCloss         )
PPT.Loss.AClossMagneticMethod             = w2kw(resultBasePoint.AClossMagneticMethod         )
PPT.Loss.IronLossTotal      = w2kw(resultBasePoint.IronLossTotal  )      
PPT.Loss.Magloss            = w2kw(resultBasePoint.Magnetloss        )  
PPT.Loss.TotalEMLoss        = w2kw(resultBasePoint.TotalEMLoss    )      


% Total Percent
PPT.Percent.Totalpercent.DCloss             = percent(resultBasePoint.DCloss       /resultBasePoint.TotalEMLoss  )
PPT.Percent.Totalpercent.AClossMagneticMethod             = percent(resultBasePoint.AClossMagneticMethod       /resultBasePoint.TotalEMLoss  )
PPT.Percent.Totalpercent.IronLossTotal      = percent(resultBasePoint.IronLossTotal/resultBasePoint.TotalEMLoss  )   
PPT.Percent.Totalpercent.Magloss            = percent(resultBasePoint.Magnetloss      /resultBasePoint.TotalEMLoss  )  
PPT.Percent.Totalpercent.TotalEMLoss        = percent(resultBasePoint.TotalEMLoss  /resultBasePoint.TotalEMLoss  )   

%%\
PPT.kw=w2kw(resultBasePoint.OutputPower)
% Loss Ratio  
resultBasePoint.DCloss/resultBasePoint.TotalEMLoss
resultBasePoint.AClossMagneticMethod/resultBasePoint.TotalEMLoss*100
resultBasePoint.IronLossTotal/resultBasePoint.TotalEMLoss*100

FWPPT.loss.DCloss        =w2kw(resultFW.DCloss        )
FWPPT.loss.AClossMagneticMethod        =w2kw(resultFW.AClossMagneticMethod        )
FWPPT.loss.IronLossTotal =w2kw(resultFW.IronLossTotal )
FWPPT.loss.Magloss       =w2kw(resultFW.Magloss       )
FWPPT.loss.TotalEMLoss   =w2kw(resultFW.TotalEMLoss   )

FWPPT.percent.loss.DCloss        =percent(FWPPT.loss.DCloss        /FWPPT.loss.TotalEMLoss)
FWPPT.percent.loss.AClossMagneticMethod        =percent(FWPPT.loss.AClossMagneticMethod        /FWPPT.loss.TotalEMLoss)
FWPPT.percent.loss.IronLossTotal =percent(FWPPT.loss.IronLossTotal /FWPPT.loss.TotalEMLoss)
FWPPT.percent.loss.Magloss       =percent(FWPPT.loss.Magloss       /FWPPT.loss.TotalEMLoss)
FWPPT.percent.loss.TotalEMLoss   =percent(FWPPT.loss.TotalEMLoss   /FWPPT.loss.TotalEMLoss)




resultBasePoint.Magnetloss/resultBasePoint.TotalEMLoss*100

resultBasePoint.DCloss/resultBasePoint.OutputPower*100
resultBasePoint.AClossMagneticMethod/resultBasePoint.OutputPower*100
resultBasePoint.IronLossTotal/resultBasePoint.OutputPower*100
resultBasePoint.Magnetloss/resultBasePoint.OutputPower*100


resultBasePoint.DCloss/resultBasePoint.ElectromagneticPower*100
resultBasePoint.AClossMagneticMethod/resultBasePoint.ElectromagneticPower*100
resultBasePoint.IronLossTotal/resultBasePoint.ElectromagneticPower*100
resultBasePoint.Magnetloss/resultBasePoint.ElectromagneticPower*100

%[text] %[text:anchor:H_6A420F28] ## Phasor Diagram
% from EmagPhasordiagram Data
ResultMotorcadEmagPhasorDiagram= getPhasorDiagramMcadEmag(mcad)
ResultMotorcadEmagPhasorDiagram.p=8
input_obj=ResultMotorcadEmagPhasorDiagram
blondelPhasorDiagram(ResultMotorcadEmagPhasorDiagram)

lambda_d=ResultMotorcadEmagPhasorDiagram.FluxLinkageLoad_D
lambda_q=ResultMotorcadEmagPhasorDiagram.FluxLinkageLoad_Q
i_d=ResultMotorcadEmagPhasorDiagram.RMSPhaseCurrent_D
i_q=ResultMotorcadEmagPhasorDiagram.RMSPhaseCurrent_Q
R_s=McadRaw.ArmatureWindingResistancePh
PhaseVoltageRms=McadRaw.PhaseVoltage
% 약계자없이
omega_e_max = findMaxOmegaE(lambda_d, lambda_q, i_d, i_q, R_s, PhaseVoltageRms)
maxRPM=OmegaE2rpm(omega_e_max,4)

% Manual Post
[McadRaw,mcadTable]=getMcadEmagData4Phasor(mcad(1))
combineStruct=calcMcadPostPhasorDiagram(McadRaw,10000)
isfield(combineStruct,'VRMSinductanceDropDaxis')
plotBlondelPhasorDiagram(combineStruct)
blondelPhasorDiagram(combineStruct)

%[appendix]{"version":"1.0"}
%---
%[metadata:view]
%   data: {"layout":"inline","rightPanelPercent":40}
%---
