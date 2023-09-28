function settingTable = defMcadLabCalcSetting()
    % Calculation - General
    input.DCBusVoltage                               = 800;      % Drive - DC Bus Voltage
    input.ModulationIndex_MotorLAB                   = 0.95;     % Drive - Maximum Modulation Index
    input.OperatingMode_Lab                          = 0;        % Drive - Operating Mode : Motor
    input.ControlStrat_MotorLAB                      = 0;        % Drive - Control Stratey : Maximum Torque/Amp
    input.DCCurrentLimit_Lab                         = 0;        % Drive - DC Current Limit : None

    input.MagnetLossBuildFactor                      = 1 ;       % Losses - Magnet Loss Build Factor
    input.StatorIronLossBuildFactor                  = 1.5 ;       % Losses - Iron Loss Build Factors - Stator
    input.RotorIronLossBuildFactor                   = 1.5 ;       % Losses - Iron Loss Build Factors - Rotor

    input.TurnsCalc_MotorLAB                         = 1;        % Scaling - Turns / Coil - Calculation

    input.TwindingCalc_MotorLAB                      = 65;       % Temperatures - Stator Winding Temperature - Calculation temperature
    input.StatorCopperFreqCompTempExponent           = 1;        % Temperatures - Stator Winding Temperature - AC Loss Temperature Scailing - Temperature Exponent
    input.TmagnetCalc_MotorLAB                       = 65;       % Temperatures - Magnet Temperature - Calculation temperature

    % Elecromagnetic
    input.EmagneticCalcType_Lab                     = 1;        % Calculation - Calculation Type : Efficiency Map
    input.SmoothMap_MotorLAB                        = true;     % Calculation - Options - Smooth Map : "On"
    input.PowerLim_MotorLAB                         = false;    % Calculation - Options - Power Limit : "Off"
    input.PowerLimVal_MotorLAB                      = 1000000;  % Calculation - Options - Power Limit - Max Power
    input.SpeedMax_MotorLAB                         = 6000;    % Calculation - Speed - Maximum
    input.Speedinc_MotorLAB                         = 25;      % Calculation - Speed - Step Size
    input.SpeedMin_MotorLAB                         = 0;      % Calculation - Speed - Minimum
    input.Imax_MotorLAB                             = 900;       %
    input.Imax_RMS_MotorLAB                         = 900;      % Calculation - Current - Maximum (RMS)
    input.Iinc_MotorLAB                             = 100;       % Calculation - Current - No. of Increments
    input.Imin_MotorLAB                             = [];       %
    input.Imin_RMS_MotorLAB                         = 0;       % Calculation - Current - Minimum (RMS)
    input.TorqueMax_MotorLAB                        = [];       %
    input.TorqueInc_MotorLAB                        = [];       %
    input.MinTorque_MotorLAB                        = [];       %
%% 수정 x
    % 필요한 변수들을 추가할지 결정하는 조건을 적용하고 필드 추가
    data = {
        "DCBusVoltage"                                 , input.DCBusVoltage;
        "ModulationIndex_MotorLAB"                     , input.ModulationIndex_MotorLAB;
        "OperatingMode_Lab"                            , input.OperatingMode_Lab;
        "ControlStrat_MotorLAB"                        , input.ControlStrat_MotorLAB;
        "DCCurrentLimit_Lab"                           , input.DCCurrentLimit_Lab;
        "MagnetLossBuildFactor"                        , input.MagnetLossBuildFactor;
        "StatorIronLossBuildFactor"                    , input.StatorIronLossBuildFactor;
        "RotorIronLossBuildFactor"                     , input.RotorIronLossBuildFactor;
        "TurnsCalc_MotorLAB"                           , input.TurnsCalc_MotorLAB;
        "TwindingCalc_MotorLAB"                        , input.TwindingCalc_MotorLAB;
        "StatorCopperFreqCompTempExponent"             , input.StatorCopperFreqCompTempExponent;
        "TmagnetCalc_MotorLAB"                         , input.TmagnetCalc_MotorLAB;
        "EmagneticCalcType_Lab"                        , input.EmagneticCalcType_Lab;
        "SmoothMap_MotorLAB"                           , input.SmoothMap_MotorLAB;
        "PowerLim_MotorLAB"                            , input.PowerLim_MotorLAB;
        "PowerLimVal_MotorLAB"                         , input.PowerLimVal_MotorLAB;
        "SpeedMax_MotorLAB"                            , input.SpeedMax_MotorLAB;
        "Speedinc_MotorLAB"                            , input.Speedinc_MotorLAB;
        "SpeedMin_MotorLAB"                            , input.SpeedMin_MotorLAB;
        "Imax_MotorLAB"                                , input.Imax_MotorLAB;
        "Imax_RMS_MotorLAB"                            , input.Imax_RMS_MotorLAB;
        "Iinc_MotorLAB"                                , input.Iinc_MotorLAB;
        "Imin_RMS_MotorLAB"                            , input.Imin_RMS_MotorLAB;
    };
    
    % 조건에 따라 필요한 변수 추가
    if input.PowerLim_MotorLAB == true || input.PowerLim_MotorLAB == 1
        data = [data; {"PowerLimVal_MotorLAB", input.PowerLimVal_MotorLAB}];
    end

    % 테이블 생성
    settingTable = cell2table(data, 'VariableNames', {'AutomationName', 'CurrentValue'});
end
