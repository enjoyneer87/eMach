
data = {
    "HousingType"                        , [];
    "Housing_Dia"                        , 260;
    "Stator_Lam_Length"                  , [];
    "Motor_Length"                       , [];
    "EWdg_Overhang_[F]_Used"             , [];
    "EWdg_Overhang_[R]_Used"             , [];
    "Housing_Water_Jacket"               , 1;
    "Shaft_Spiral_Groove"                , 1;
    "Spray_Cooling"                      , 1;
    "FloodedCooling"                     , 1;
    "HousingWJ_Volume_Flow_Rate_Total"   , 20;
    "WJ_Parallel_Paths"                  , 1;
    "AxialSliceDefinition"               , 3;
    "CuboidalkValueDefinition"           , [];
    "SprayCoolingSubmerged"              , 0;
};

coolingSystemTable = cell2table(data, "VariableNames", ["AutomationName", "CurrentValue"]);
charValues = cellfun(@num2str, coolingSystemTable.CurrentValue, 'UniformOutput', false);
coolingSystemTable.CurrentValue = charValues;

clear data
clear charValues