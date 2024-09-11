function  [fitResult, scaledDataInfo,DataSet] =interpLossdqhSpeedSetFromMCADTable(MCADLinkTable,MachineData,nTarget)
    
    
% dev
% ScaledLossFitResult=calcSpeedScaledLossFromMcadLinkTable(idm,iqm,MCADLinkTable,MachineData,nTarget)
% nTarget=5800
freqEOp                 =rpm2freqE(nTarget,MachineData.MotorCADGeo.Pole_Number/2)                                 ;      
freqEBuild              =rpm2freqE(MachineData.LabBuildData.n2ac_MotorLAB,MachineData.MotorCADGeo.Pole_Number/2)  ;                      
% freqEOp/freqEBuild

%% Scale Speed Dependent Loss
SpeedScaledMcadTable                    =scaleSpeedIronLossFromMcadLinkTable(MCADLinkTable,MachineData,freqEOp)                ; 
Pcoil_AC_scaledTable                    =scaleSpeedACLossFromMcadLinkTable(SpeedScaledMcadTable, MachineData, nTarget)       ;             
SpeedScaledMcadTable                    =updateTableValues(SpeedScaledMcadTable,Pcoil_AC_scaledTable);
Wmag_ref                                =MCADLinkTable.("Magnet Loss");
Wmag_scaled                             =scaleSpeedMagnetLoss(Wmag_ref, MachineData, nTarget);
SpeedScaledMcadTable.("Magnet Loss")    =Wmag_scaled;
% (freqEOp/freqEBuild)^2
% MCADLinkTable.("Hysteresis Iron Loss (Rotor Back Iron)")
% SpeedScaledMcadTable.("Hysteresis Iron Loss (Rotor Back Iron)")

varNameList                             = SpeedScaledMcadTable.Properties.VariableNames;
[fitResult, scaledDataInfo,DataSet]      =interpLossFitResultFromMCadTable(SpeedScaledMcadTable, varNameList);
 
scaledDataInfo.freqEOp                  = freqEOp;
scaledDataInfo.freqEBuild               = freqEBuild;
scaledDataInfo.nTarget                  = nTarget;
% DataSet.originDqTable
% DataSet.originDqTable
% %% Eddy Loss
% varNameList=SpeedScaledMcadTable.Properties.VariableNames;
% HysVarIndexList   =find(contains(varNameList,'Hys'));
% EddyVarIndexList  =find(contains(varNameList,'Eddy'));
% ACVarIndexList    =find(contains(varNameList,'AC Copper'));
% MagVarIndexList   =find(contains(varNameList,'Magnet'));
% % 
% % FluxDVarIndexList=find(contains(varNameList,'Flux Linkage D'))
% % FluxqVarIndexList=find(contains(varNameList,'Flux Linkage Q'))

% %% Interp Loss
% % Hys Fit
% for HysIndex=1:length(HysVarIndexList)
% HysVarName=varNameList{HysVarIndexList(HysIndex)};
% HysfitList{HysIndex}.Name=HysVarName;
% [HysfitList{HysIndex}.fitReulst, ~, ~] = createInterpDataSet(SpeedScaledMcadTable,HysVarName );
% end

% % Eddy Fit
% for EddyIndex=1:length(EddyVarIndexList)
% EddyVarName=varNameList{EddyVarIndexList(EddyIndex)};
% EddyfitList{EddyIndex}.Name=EddyVarName;
% [EddyfitList{EddyIndex}.fitReulst, ~, ~] = createInterpDataSet(SpeedScaledMcadTable,EddyVarName );
% end
% % AC Fit 
% for ACIndex=1:length(ACVarIndexList)
% ACLossVarName=varNameList{ACVarIndexList(ACIndex)};
% ACLossfitList{ACIndex}.Name=ACLossVarName
% [ACLossfitList{ACIndex}.fitReulst, ~, ~] = createInterpDataSet(SpeedScaledMcadTable,ACLossVarName );
% end
% % Mag Fit
% for MagIndex=1:length(MagVarIndexList)
% MagLossVarName=varNameList{MagVarIndexList(MagIndex)};
% MagLossfitList{MagIndex}.Name=MagLossVarName;
% [MagLossfitList{MagIndex}.fitReulst, ~, DataSet] = createInterpDataSet(SpeedScaledMcadTable,MagLossVarName );
% end

% % % lambda Fit
% % [FluxLinkDFit,~,~]=createInterpDataSet(SpeedScaledMcadTable,'Flux Linkage D');
% % [FluxLinkQFit,~,~]=createInterpDataSet(SpeedScaledMcadTable,'Flux Linkage Q');
% Ploss_dqh.fitResult.HysFit  =HysfitList;
% Ploss_dqh.fitResult.EddyFit =EddyfitList;
% Ploss_dqh.fitResult.ACFit   =ACLossfitList;
% Ploss_dqh.fitResult.MagFit  =MagLossfitList;

end
