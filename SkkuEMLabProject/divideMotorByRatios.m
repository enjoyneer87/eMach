function motorSplitStruct = divideMotorByRatios(motorRequiredCurve, motorRatios)
    if sum(motorRatios) ~= 1
        error('motorRatios의 합계는 1이어야 합니다.');
    end

    motorSplitStruct    = struct();    
    singleMotorRequiredCurve = motorRequiredCurve;
    singleMotorRequiredCurve.motor_max_t = singleMotorRequiredCurve.motor_max_t * motorRatios;
    % singleMotorRequiredCurve.motor_max_p = singleMotorRequiredCurve.motor_max_p * motorRatios;
    singleMotorRequiredCurve.motor_max_kW = singleMotorRequiredCurve.motor_max_kW * motorRatios;
    
    motorSplitStruct.MotorCurve             =motorRequiredCurve;
    motorSplitStruct.dividedMotorCurve      =singleMotorRequiredCurve;
    motorSplitStruct.motorNumber            =width(singleMotorRequiredCurve.motor_max_t);
    motorSplitStruct.motorRatios            =motorRatios;

end
