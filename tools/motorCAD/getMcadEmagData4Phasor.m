function [McadRaw,mcadTable]=getMcadEmagData4Phasor(mcad)
mcadTable=defMcadTable('magnetic')
mcadTable2=defMcadTable('miscellaneous')
mcadTable3=defMcadTable('Dimensions')
mcadTable=[mcadTable;mcadTable2;mcadTable3]
PhasorCalcRawList={
'Pole_Number',
'ShaftSpeed',
'RmsBackEMFPhase',
'FluxLinkageLoad',
'FluxLinkageLoad_D',
'FluxLinkageLoad_Q',
'FluxLinkageQAxisCurrent_D',
'FluxLinkageQAxisCurrent_Q',
'PhaseAdvance',
'RMSPhaseCurrent',
'InductanceLoad_D',
'InductanceLoad_Q',
'ArmatureWindingResistancePh',
'ArmatureConductor_Temperature',
'ArmatureMLT',
'ArmatureEWdgMLT_Calculated',
'EndWindingResistance_Lab',
'Resistance_MotorLAB',
'DCBusVoltage',
'PhaseVoltage'
}
mcadTable=filterMCADTable(mcadTable,PhasorCalcRawList,'exact');
mcadTable=getMcadTableVariable(mcadTable,mcad);
mcadTable = convertMCADTableCurrentValueToDouble(mcadTable);
% mcadTable = filterMCADTableZeroValue(mcadTable);
mcadEmagPhasorRawStruct = MCADtable2Struct(mcadTable);
McadRaw=mcadEmagPhasorRawStruct;
% PhaseAdvance
% RMSPhaseCurrent
% RMSPhaseCurrent_D
% RMSPhaseCurrent_Q
% FluxLinkageQAxisCurrent_D
% InductanceDxCurrent_D
% InductanceQxCurrent_Q
%% calc Phase Resistivity Voltage
% RMSPhaseResistiveVoltage_D
% RMSPhaseResistiveVoltage_Q
%% calc Phase Reactive Voltage
% rms Phase Voltage
% PhaseVoltage
% PhasorLoadAngle
% PhasorPowerFactorAngle