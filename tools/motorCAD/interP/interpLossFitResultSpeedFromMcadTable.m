function [Ploss_dqh, SpeedScaledInfo] = interpLossFitResultSpeedFromMcadTable(MCADLinkTable, MachineData, nTargetList)
    
    for nIndex = 1:length(nTargetList)
        nTarget = nTargetList(nIndex);
        % Prepare the data & Create Sfit
        freqEOp =    rpm2freqE(nTarget, MachineData.MotorCADGeo.Pole_Number/2);     
        freqEBuild = rpm2freqE(MachineData.LabBuildData.n2ac_MotorLAB, MachineData.MotorCADGeo.Pole_Number/2);
        
        % Scale Speed Dependent Loss
        SpeedScaledMcadTable = scaleSpeedIronLossFromMcadLinkTable(MCADLinkTable, MachineData, freqEOp); 
        Pcoil_AC_scaledTable = scaleSpeedACLossFromMcadLinkTable(SpeedScaledMcadTable, MachineData, nTarget);             
        SpeedScaledMcadTable = updateTableValues(SpeedScaledMcadTable, Pcoil_AC_scaledTable);
        Wmag_ref = MCADLinkTable.("Magnet Loss");
        Wmag_scaled = scaleSpeedMagnetLoss(Wmag_ref, MachineData, nTarget);
        SpeedScaledMcadTable.("Magnet Loss") = Wmag_scaled;
        
        varNameList = SpeedScaledMcadTable.Properties.VariableNames;
        [Ploss_dqh(nIndex).fitResult, SpeedScaledInfo(nIndex).LossDataInfo] = interpLossFitResultFromMCadTable(SpeedScaledMcadTable, varNameList);
        
        SpeedScaledInfo(nIndex).freqEOp = freqEOp;
        SpeedScaledInfo(nIndex).freqEBuild = freqEBuild;
        SpeedScaledInfo(nIndex).nTarget = nTarget;
        
    end

    % return; % Return the results
end
