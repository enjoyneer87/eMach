function [smallPoint,vehiclePerformData]=tempCallDecideSimulationTargetPoint(matData,motorSplitStruct,vehiclePerformData)
    motorCurve=table();
    motorCurve.rpm           =matData.Speed(:,end);
    motorCurve.motor_max_t   =matData.Shaft_Torque(:,end);
    motorCurve.motor_max_kW  =matData.Shaft_Power(:,end);
    
    dividedTablesCell = splitTable(motorSplitStruct.dividedMotorCurve);
    firstMotorRequired=dividedTablesCell{1};
    
    [newMotorCurve, newMotorRequiredCurve1] = interpolateTables(motorCurve, firstMotorRequired);
    vehiclePerformData.power_kw             = newMotorRequiredCurve1.motor_max_kW;
    %[TC] Including Plot 6,7
    smallPoint                              = decideSimulationTargetPoint(newMotorCurve,newMotorRequiredCurve1);  

end