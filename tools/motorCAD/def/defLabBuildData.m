function LabBuildData =defLabBuildData(mcad)
  [~, LabBuildData.CalcTypeCuLoss_MotorLAB]          = mcad.GetVariable('CalcTypeCuLoss_MotorLAB')     ;
  % [~,  % AC Lo;
  [~, LabBuildData.n2ac_MotorLAB]                    = mcad.GetVariable('n2ac_MotorLAB')              ;
  [~, LabBuildData.AcLossFreq_MotorLAB]              = mcad.GetVariable('AcLossFreq_MotorLAB')         ;
  % [~, ]                = %Iron Lo;
  [~, LabBuildData.IronLossCalc_Lab]                 = mcad.GetVariable('IronLossCalc_Lab')           ;
  [~, LabBuildData.FEALossMap_RefSpeed_Lab]          = mcad.GetVariable('FEALossMap_RefSpeed_Lab')     ;
  % [~, ]                = %%Magnet Lo;
  [~, LabBuildData.MagnetLossCalc_Lab]               = mcad.GetVariable('MagnetLossCalc_Lab')         ;
  [~, LabBuildData.MagLossCoeff_MotorLAB]            = mcad.GetVariable('MagLossCoeff_MotorLAB')      ;
  % [~, ]                = % Banding Lo;
  [~, LabBuildData.BandingLossCoefficient_Lab]       = mcad.GetVariable('BandingLossCoefficient_Lab')  ;
  [~, LabBuildData.BandingLossCalc_Lab]              = mcad.GetVariable('BandingLossCalc_Lab');
end