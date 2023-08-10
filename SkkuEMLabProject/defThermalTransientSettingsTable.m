% Thermal>OP포인트 온도상승해석)

% ThermalCalcType                     = 1  
% ThermalModelSize                    = 0
% ThermalModelType                    = 0
% TransientCalculationType            = 0
% 
% EndPoint_Definition                 = 2
% UseEndPointTempLimit_ArmatureWdg    = 1
% EndPointTempLimit_ArmatureWdg       = 180
% UseEndPointTempLimit_Magnet         = 1
% EndPointTempLimit_Magnet            = 150
% 
% EndPoint_TimeBetweenPoints          =1
% 
% Simple_Transient_Definition         =1
% Simple_Transient_Torque             =[];
% 
% InitialTransientTemperatureOption   =[];

data = {
    "ThermalCalcType"                    , 1;
    "ThermalModelSize"                   , 0;
    "ThermalModelType"                   , 0;
    "TransientCalculationType"           , 0;
    "EndPoint_Definition"                , 2;
    "UseEndPointTempLimit_ArmatureWdg"   , 1;
    "EndPointTempLimit_ArmatureWdg"      , 180;
    "UseEndPointTempLimit_Magnet"        , 1;
    "EndPointTempLimit_Magnet"           , 150;
    "EndPoint_TimeBetweenPoints"         , 1;
    "Simple_Transient_Definition"        , 1;
    "Simple_Transient_Torque"            , [];
    "InitialTransientTemperatureOption"  , [];
};

thermalSettingsTable = cell2table(data, "VariableNames", ["AutomationName", "CurrentValue"]);
clear data