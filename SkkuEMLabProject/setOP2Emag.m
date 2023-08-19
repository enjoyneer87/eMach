function setOP2Emag(speed,ShaftTorque,mcad)
    mcad.SetVariable('SpeedDemand_MotorLAB',speed);
    mcad.SetVariable('OpPointSpec_MotorLAB',0);
    mcad.SetVariable('TorqueDemand_MotorLAB',ShaftTorque);
    mcad.SetVariable('LabMagneticCoupling',1)
    mcad.CalculateOperatingPoint_Lab();
end