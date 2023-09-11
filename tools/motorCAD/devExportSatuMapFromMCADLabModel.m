function SatuMapFilePath=devExportSatuMapFromMCADLabModel(SatuMapFilePath,mcad)


%% Get Lab Model Data
[~,referenceSpeed]=mcad.GetVariable('FEALossMap_RefSpeed_Lab' );
[~,Imax]          =mcad.GetVariable('MaxModelCurrent_MotorLAB');
% [~,Imax]          =mcad.GetVariable('MaxModelCurrent_MotorLAB');
MotorCADGeo=tempDefMCADMachineData4Scaling(mcad);
%%

mcad.SetVariable('SaturationMap_InputDefinition',       1);
mcad.SetVariable('SaturationMap_CalculationMethod',     0);
mcad.SetVariable('SaturationMap_Current_D_Max',       0);
mcad.SetVariable('SaturationMap_Current_D_Step',      Imax/100);
mcad.SetVariable('SaturationMap_Current_D_Min',       -Imax);
mcad.SetVariable('SaturationMap_Current_Q_Max',       Imax);
mcad.SetVariable('SaturationMap_Current_Q_Step',      Imax/100);
mcad.SetVariable('SaturationMap_Current_Q_Min',       0);


mcad.SetVariable('SaturationMap_Export',      1);
mcad.SetVariable('LossMap_Export',            1);
mcad.SetVariable('LossMap_Speed',             referenceSpeed);

mcad.SetVariable('SaturationMap_ExportFile',            SatuMapFilePath);
mcad.CalculateSaturationMap();
SatuMapData=load(SatuMapFilePath);
SatuMapData.MotorCADGeo=MotorCADGeo;
clear('mcad','referenceSpeed','Imax','ans')
save(SatuMapFilePath,'-mat');

end