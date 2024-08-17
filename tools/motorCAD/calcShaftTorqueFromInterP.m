
function TShaft=calcShaftTorqueFromInterP(idm,iqm,MTPAFitResult,MCADLinkTable,MachineData,nTarget)

%% Fit Inductance 


% [LdFitResult,LqFitResult,PMFluxFitResult,FitLdqPMTable] = fitLdLqMapsFromMCADTable(MCADLinkTable);

PMFluxFitResult=MTPAFitResult.PMFluxFitResult;
LdFitResult=MTPAFitResult.LdFitResult;
LqFitResult=MTPAFitResult.LqFitResult;


%% Speed Scale Loss -> calcSpeedScaledLossFromMcadLinkTable

% dev
% ScaledLossFitResult=calcSpeedScaledLossFromMcadLinkTable(idm,iqm,MCADLinkTable,MachineData,nTarget)
% nTarget=5800
% freqEOp                 =rpm2freqE(nTarget,MachineData.MotorCADGeo.Pole_Number/2)                                 ;      
% freqEBuild              =rpm2freqE(MachineData.LabBuildData.n2ac_MotorLAB,MachineData.MotorCADGeo.Pole_Number/2)  ;                      
% % freqEOp/freqEBuild

% SpeedScaledMcadTable          =scaleSpeedIronLossFromMcadLinkTable(MCADLinkTable,MachineData,freqEOp)                ; 
% Pcoil_AC_scaledTable         = scaleSpeedACLossFromMcadLinkTable(SpeedScaledMcadTable, MachineData, nTarget)       ;             

% % (freqEOp/freqEBuild)^2
% % MCADLinkTable.("Hysteresis Iron Loss (Rotor Back Iron)")
% % SpeedScaledMcadTable.("Hysteresis Iron Loss (Rotor Back Iron)")


% SpeedScaledMcadTable=updateTableValues(SpeedScaledMcadTable,Pcoil_AC_scaledTable);
% Wmag_ref=MCADLinkTable.("Magnet Loss");

% Wmag_scaled = scaleSpeedMagnetLoss(Wmag_ref, MachineData, nTarget);
% SpeedScaledMcadTable.("Magnet Loss")=Wmag_scaled;

% varNameList=SpeedScaledMcadTable.Properties.VariableNames;
% HysVarIndexList   =find(contains(varNameList,'Hys'));
% EddyVarIndexList  =find(contains(varNameList,'Eddy'));
% ACVarIndexList    =find(contains(varNameList,'AC Copper'));
% MagVarIndexList   =find(contains(varNameList,'Magnet'));
% % 
% % FluxDVarIndexList=find(contains(varNameList,'Flux Linkage D'))
% % FluxqVarIndexList=find(contains(varNameList,'Flux Linkage Q'))

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
% [MagLossfitList{MagIndex}.fitReulst, ~, ~] = createInterpDataSet(SpeedScaledMcadTable,MagLossVarName );
% end
% % lambda Fit
% [FluxLinkDFit,~,~]=createInterpDataSet(SpeedScaledMcadTable,'Flux Linkage D');
% [FluxLinkQFit,~,~]=createInterpDataSet(SpeedScaledMcadTable,'Flux Linkage Q');
%% PPostLoss2TPoseLoss

%% Loss @idm,iqm
% [idm,iqm]=pkgamma2dq(Is,PhaseAdvance)  % pk, gamma

%%  TotalElecLossFromFitResultStr
TotalHys=0;
for HysIndex=1:length(HysVarIndexList)
   HysLossList{HysIndex}.Name=varNameList{HysVarIndexList(HysIndex)};
   HysLossList{HysIndex}.Value=HysfitList{HysIndex}.fitReulst(idm,iqm);
   TotalHys  = TotalHys+HysLossList{HysIndex}.Value;
end

TotalEddy=0;
for EddyIndex=1:length(EddyVarIndexList)
   EddyLostList{EddyIndex}.Name=varNameList{EddyVarIndexList(EddyIndex)};
   EddyLostList{EddyIndex}.Value=EddyfitList{EddyIndex}.fitReulst(idm,iqm);
   TotalEddy  = TotalEddy+EddyLostList{EddyIndex}.Value;
end

TotalAC=0;
for ACIndex=1:length(ACVarIndexList)
   ACLostList{ACIndex}.Name=varNameList{ACVarIndexList(ACIndex)}        ;        
   ACLostList{ACIndex}.Value=ACLossfitList{ACIndex}.fitReulst(idm,iqm)  ;            
   TotalAC  = TotalAC+ACLostList{ACIndex}.Value;
end

MagnetLoss=0;
for MagIndex=1:length(MagVarIndexList)
   MagLossList{MagIndex}.Name=varNameList{MagVarIndexList(MagIndex)}        ;    
   MagLossList{MagIndex}.Value=MagLossfitList{MagIndex}.fitReulst(idm,iqm)  ;        
   MagnetLoss  = MagnetLoss+MagLossList{MagIndex}.Value;
end


%% [TB] IronLoss Factor

PPostLoss =(TotalHys+TotalEddy)*1.5*freqEBuild+TotalAC+MagnetLoss;
(TotalHys+TotalEddy)/1000*freqEBuild*1.5;
TACLoss= power2torque(TotalAC/1000,nTarget);
TPostLoss = power2torque(PPostLoss/1000,nTarget);

%% [TB] Windage Loss & Bearing Loss


%% 
%% Calc DQ Torque

psi_pm=PMFluxFitResult(idm,iqm);
Ld    =LdFitResult(idm,iqm);
Lq    =LqFitResult(idm,iqm);

TorqueDqSingle= calcDQFluxTorque(idm,iqm,FluxLinkDFit(idm,iqm),FluxLinkQFit(idm,iqm),MachineData.MotorCADGeo.Pole_Number)                          ; 
TorqueLDqSingle =calcDQLTorque(idm, iqm, MachineData.MotorCADGeo.Pole_Number,PMFluxFitResult(idm,iqm), LdFitResult(idm,iqm), LqFitResult(idm,iqm)) ;                         
TShaft = TorqueLDqSingle-TPostLoss;


end