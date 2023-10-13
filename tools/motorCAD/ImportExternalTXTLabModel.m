function ImportExternalTXTLabModel(LabLinkTxtPath,BuildData,mcad,ScaledMachineData)

% from devImportExternalTXTSatuModel

    % 'Motor-CAD EMag'
    % 'Ansys'
    %'Custom (Advanced)'
    MotorCADGeo=BuildData.MotorCADGeo;
    LabBuildData=BuildData.LabBuildData;

    %% Lab Build Variable
    mcad.SetVariable('ElectroLink_MotorLAB','Custom (Advanced)');
    mcad.SetMotorLABContext()
    mcad.SetVariable('CalcTypeCuLoss_MotorLAB',     LabBuildData.CalcTypeCuLoss_MotorLAB);

    % AC Loss
    mcad.SetVariable('n2ac_MotorLAB',               LabBuildData.n2ac_MotorLAB);
    mcad.SetVariable('AcLossFreq_MotorLAB',         LabBuildData.AcLossFreq_MotorLAB);
    %Iron Loss
    mcad.SetVariable('IronLossCalc_Lab',            LabBuildData.IronLossCalc_Lab);
    mcad.SetVariable('FEALossMap_RefSpeed_Lab',     LabBuildData.FEALossMap_RefSpeed_Lab);
    %%Magnet Loss
    mcad.SetVariable('MagnetLossCalc_Lab',          LabBuildData.MagnetLossCalc_Lab);
    mcad.SetVariable('MagLossCoeff_MotorLAB',       LabBuildData.MagLossCoeff_MotorLAB);
    % Banding Loss
    mcad.SetVariable('BandingLossCalc_Lab',         LabBuildData.BandingLossCalc_Lab);
    mcad.SetVariable('BandingLossCoefficient_Lab',  LabBuildData.BandingLossCoefficient_Lab);
    
    %%    
    if nargin>3
    setMcadVariable(ScaledMachineData,mcad);
    mcad.ShowMagneticContext()
    if MotorCADGeo.Armature_CoilStyle==0  % 환선
        mcad.SetVariable('Armature_Winding_Definition',2); 
        mcad.SetVariable('RequestedGrossSlotFillFactor',MotorCADGeo.GrossSlotFillFactor);
        mcad.SetVariable('GeometryParameterisation',1);
    elseif MotorCADGeo.Armature_CoilStyle==1
        mcad.SetVariable('Copper_Width',ScaledMachineData.Copper_Width );
        mcad.SetVariable('Copper_Height',ScaledMachineData.Copper_Height);
    end
    end

    mcad.ClearModelBuild_Lab();
    mcad.LoadExternalModel_Lab(LabLinkTxtPath);

end