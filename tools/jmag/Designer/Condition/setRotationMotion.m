function setRotationMotion(app,RPM)
% studyObj=curStudyObj

ModelObj=app.GetCurrentModel;
studyObj=app.GetCurrentStudy;
%%
if studyObj.GetCondition('Rotation').IsValid
    RotConObj=studyObj.GetCondition('Rotation');
else
    RotConObj=studyObj.CreateCondition('RotationMotion','Rotation');
end

%% AddSet 
RotConObj.AddSetFromModel('Rotor',int32(0));
% RotConObj.IsValid
% RotConObj.GetParts
% RotConObj.AddSet(ModelObj.GetSetList().GetSet("Rotor"), 0);


RotConObj.SetValue('AngularVelocity',RPM)

%% Initial Position
Dtable=studyObj.GetDesignTable();
Pole=Dtable.GetEquation('POLES').GetValue;
Slot=Dtable.GetEquation('SLOTS').GetValue;
[~,~,OneSlotAngle]=calcMotorPeriodicity(Pole,Slot);
RotConObj.SetValue('InitialRotationAngle',OneSlotAngle)
% JmagPropTab=convertChar2JMAGPropertiesTable(RotConObj.GetPropertyTable);


end