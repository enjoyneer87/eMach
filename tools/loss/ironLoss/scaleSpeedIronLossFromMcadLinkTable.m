function SpeedScaledMcadTable=scaleSpeedIronLossFromMcadLinkTable(MCADLinkTable,MachineData,freqEOp)

% MachineData=refLABBuildData;
% MCADLinkTable=originLabLinkTable;

SpeedScaledMcadTable=MCADLinkTable;

%%Freqeuncy
freqEBuild=rpm2freqE(MachineData.LabBuildData.n2ac_MotorLAB,MachineData.MotorCADGeo.Pole_Number/2);
% freqEOp   =rpm2freqE(5800,MachineData.MotorCADGeo.Pole_Number/2)


%% VarName 
varName=MCADLinkTable.Properties.VariableNames;

%% Move Scale Iron Loss 2 ScaledTable
HysVarIndexList  =find(contains(varName,'Hys'));
EddyVarIndexList =find(contains(varName,'Eddy'));
for Index=1:length(HysVarIndexList)
HysVarIndex=HysVarIndexList(Index);
WHys_ref=MCADLinkTable.(varName{HysVarIndex});
SpeedScaledMcadTable.(varName{HysVarIndex})= scaleSpeedHysLoss(WHys_ref, freqEBuild, freqEOp);
end

for Index=1:length(EddyVarIndexList)
EddyVarIndex=EddyVarIndexList(Index);
WEddy_ref=MCADLinkTable.(varName{EddyVarIndex});
SpeedScaledMcadTable.(varName{EddyVarIndex})= scaleSpeedEddyLoss(WEddy_ref, freqEBuild, freqEOp);
end



end