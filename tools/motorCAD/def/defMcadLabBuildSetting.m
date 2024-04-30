function settingTable = defMcadLabBuildSetting()
    % Model Build
    input.ModelType_MotorLAB                        = 2;
    input.SatModelPoints_MotorLAB                   = 1;
    
    if input.SatModelPoints_MotorLAB == 2
        input.ModelBuildPoints_Current_Lab          = [];
        input.ModelBuildPoints_Gamma_Lab            = [];
    end
    
    input.LossModel_Lab                             = 1;
    input.ACLossMethod_Lab                          = 0; % Hybrid, 1: Full Fea
    
    %
    input.BuildSatModel_MotorLAB                    =1;
    input.BuildLossModel_MotorLAB                   =1;
    % Loss Model
    if input.LossModel_Lab == 2
        input.CalcTypeCuLoss_MotorLAB               = [];
        input.IronLossCalc_Lab                      = [];
        input.BandingLossCalc_Lab                   = [];
        input.n2ac_MotorLAB                         = [];
        input.FEALossMap_RefSpeed_Lab               = [];
    end
    
    % Machine Parameters
    input.ModelBuildSpeed_MotorLAB                  =[];
    input.MaxModelCurrent_MotorLAB              =[];

    input.MaxModelCurrent_RMS_MotorLAB              =[];
    % Setting
    input.CurrentSpec_MotorLAB                      = 0;
    
    % Model Settings
    input.NonSalient_MotorLAB                       = 0;
    
    % Saturation Model Method
    input.SaturationModelMethod_Lab                 = 1;
    input.SaturationModelInterpolation_Lab          = 0;

    % Adjustment Factors
    input.XEndLeak_MotorLAB                         = [];
    input.LEndWdg_MotorLAB                          = [];
    
    % Losses

    % Iron Loss Split
    input.IronLossBuildFactorDefinition             = [];
    input.ACConductorLossSplit_Lab                  = [];

    % Create a cell array for data
    data = {
        "ModelType_MotorLAB"                         , input.ModelType_MotorLAB;
        "SatModelPoints_MotorLAB"                   , input.SatModelPoints_MotorLAB;
        "LossModel_Lab"                             , input.LossModel_Lab;
        "ACLossMethod_Lab"                          , input.ACLossMethod_Lab;
        "BuildSatModel_MotorLAB"          , input.BuildSatModel_MotorLAB;
        "BuildLossModel_MotorLAB"          , input.BuildLossModel_MotorLAB;
        "ModelBuildSpeed_MotorLAB"          , input.ModelBuildSpeed_MotorLAB;
        "MaxModelCurrent_RMS_MotorLAB"          , input.MaxModelCurrent_RMS_MotorLAB;
        "MaxModelCurrent_MotorLAB"          , input.MaxModelCurrent_MotorLAB;

        "CurrentSpec_MotorLAB"                      , input.CurrentSpec_MotorLAB;
        "NonSalient_MotorLAB"                       , input.NonSalient_MotorLAB;
        "SaturationModelMethod_Lab"                 , input.SaturationModelMethod_Lab;
        "SaturationModelInterpolation_Lab"          , input.SaturationModelInterpolation_Lab;
    };

    % Adjustments based on conditions
    if input.LossModel_Lab == 2
        data = [data; {"CalcTypeCuLoss_MotorLAB", input.CalcTypeCuLoss_MotorLAB}];
        data = [data; {"IronLossCalc_Lab", input.IronLossCalc_Lab}];
        data = [data; {"BandingLossCalc_Lab", input.BandingLossCalc_Lab}];
        data = [data; {"n2ac_MotorLAB", input.n2ac_MotorLAB}];
        data = [data; {"FEALossMap_RefSpeed_Lab", input.FEALossMap_RefSpeed_Lab}];
    end

    % Create the table
    settingTable = cell2table(data, 'VariableNames', {'AutomationName', 'CurrentValue'});

    settingTable = mkMCADTablesFind5ActX(settingTable);
    
end
