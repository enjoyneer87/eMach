function magComponentList=duplicateACMagCircuitFromTemplate(PWMStudyObj,NumberMaget)
%% get Current ACMag Circuit
CircuitObj=PWMStudyObj.GetCircuit();
circuitInstanceObj=CircuitObj.GetComponentInstance("mag1");
% circuitInstanceObj.IsValid;
CIPos=circuitInstanceObj.GetPosition;
X=CIPos.GetX;
Y=CIPos.GetY;
magComponentList{1}='mag1';
%% add New Circuit Compo
for index=2:NumberMaget
magComponentName=['mag',num2str(index)];
magComponentList{index}=magComponentName;
groundComponentName='Ground';
NewMagCircuitCompoObj=PWMStudyObj.GetCircuit().CreateComponent("FEMConductor",magComponentName);
NewMagCircuitInstanceObj=PWMStudyObj.GetCircuit().CreateInstance(magComponentName, X, Y-5*index);
NewGroundCircuitCompoObj=PWMStudyObj.GetCircuit().CreateComponent("Ground");
NewGroundCircuitInstanceObj=PWMStudyObj.GetCircuit().CreateInstance(groundComponentName, X+2, Y-2-5*index);
end
