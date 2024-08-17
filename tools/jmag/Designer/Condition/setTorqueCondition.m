function setTorqueCondition(studyObj)
if studyObj.GetCondition('Torque').IsValid
TorquConObj=studyObj.GetCondition("Torque");
else
TorquConObj=studyObj.CreateCondition("Torque", "Torque");
end

TorquConObj.SetValue("TargetType", 1)
TorquConObj.SetLinkWithType("LinkedMotion", "Rotation")
TorquConObj.ClearParts()

end