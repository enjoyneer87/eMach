function DOEstr=setPostEDUWeightinDOEstr(DOEstr,TeslaSPlaidDutyCycleTable,N_d_MotorLAB,RefGearMass,HousingMass)

%     if nargin==6
%         DOEScaledBuild=varagin;
%     else
%         DOEScaledBuild=struct();
%     end
    fieldnameCellList=fieldnames(DOEstr);

    for i=1:length(fieldnameCellList)
    fieldname=fieldnameCellList{i};
    RefGearRatio = findMcadTableVariableFromAutomationName(TeslaSPlaidDutyCycleTable, 'N_d_MotorLAB');
    ModifiedGearWeight=calculateModifiedGearMass(7, N_d_MotorLAB,7, RefGearRatio,RefGearMass);
    ModifiedGearBoxMass=HousingMass+ModifiedGearWeight;
    DOEstr.(fieldname).Weight.TotalEDUWeight=ModifiedGearBoxMass+DOEstr.(fieldname).Weight.o_Weight_Act; 
    end

end