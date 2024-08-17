function setRotationMotion(studyObj,RPM)
% studyObj=curStudyObj
if studyObj.GetCondition('Rotation').IsValid
RotConObj=studyObj.GetCondition('Rotation');
else
RotConObj=studyObj.CreateCondition('RotationMotion','Rotation');
end
RotConObj.AddSetFromModel('Rotor',0);
RotConObj.SetValue('AngularVelocity',RPM)

%% Initial Position
Dtable=studyObj.GetDesignTable();
Pole=Dtable.GetEquation('POLES').GetValue;
Slot=Dtable.GetEquation('SLOTS').GetValue;
[~,~,OneSlotAngle]=calcMotorPeriodicity(Pole,Slot);
RotConObj.SetValue('InitialRotationAngle',OneSlotAngle)
% JmagPropTab=convertChar2JMAGPropertiesTable(RotConObj.GetPropertyTable);


end