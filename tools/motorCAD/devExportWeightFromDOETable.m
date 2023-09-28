function DOEScaledBuild =devExportWeightFromDOETable(DOETable,TeslaSPlaidDutyCycleTable,RefGearMass,HousingMass,varargin)


if nargin == 5
    varargin1 = varargin{1};  % varargin의 첫 번째 인수를 변수에 할당
    DOEScaledBuild = varargin1;
elseif nargin == 6
    varargin1 = varargin{1};  % varargin의 첫 번째 인수를 변수에 할당
    varargin2 = varargin{2};  % varargin의 두 번째 인수를 변수에 할당
    DOEScaledBuild = varargin1;
    N_d_MotorLAB = varargin2;
elseif nargin == 4
    DOEScaledBuild = struct();
end
% DOETable=Sensitivity1;


number=DOETable.x_;
for i=1:length(number)
structName = ['Design', num2str(number(i))];
DesignWeight.o_Weight_Act=DOETable.obj_o_Weight_Act(i);
DOEScaledBuild.(structName).Weight=DesignWeight;
RefGearRatio = findMcadTableVariableFromAutomationName(TeslaSPlaidDutyCycleTable, 'N_d_MotorLAB');
ModifiedGearWeight=calculateModifiedGearMass(7, N_d_MotorLAB,7, RefGearRatio,RefGearMass);
ModifiedGearBoxMass=HousingMass+ModifiedGearWeight;
DOEScaledBuild.(structName).Weight.TotalEDUWeight=ModifiedGearBoxMass+DesignWeight.o_Weight_Act;
end

end
