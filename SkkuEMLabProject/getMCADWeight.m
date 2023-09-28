function Weight = getMCADWeight(mcad)
    
    mcad.DoWeightCalculation();  % Weight calculation

    Weight = struct();
    [~, o_Weight_Mag                ] = mcad.GetVariable("Weight_Calc_Magnet");      % Magnet's mass 

    
    [~, o_Weight_Stat_Core          ] = mcad.GetVariable("Weight_Calc_Stator_Lam"); % Stator core's mass  
    [~, o_Weight_Rot_Core           ] = mcad.GetVariable("Weight_Calc_Rotor_Lam");  % Rotor core's mass
    [~, Weight_Shaft                ] = mcad.GetVariable("Weight_Shaft_Active");       % Shaft's mass - Total인듯   
    [~, Weight_Act_with_Shaft       ] = mcad.GetVariable("Weight_Calc_Total"); % Active mass
    [~, Weight_Total_Housing_Total  ] = mcad.GetVariable("Weight_Total_Housing_Total"); % Active mass
    % [~, Weight_Total_Housing_Total  ] = mcad.GetVariable("Weight_Internal_Calc_Housing_Total"); % Active mass

    [~, o_Weight_Wdg                ] = mcad.GetVariable("Weight_Total_Armature_Copper_Total"); % Winding's mass  Weight_Internal_Calc_Copper_Total
    % [~, o_Weight_Wdg                ] = mcad.GetVariable("Weight_Calc_Copper_Total"); % Winding's mass  Weight_Internal_Calc_Copper_Total

    
    Weight.o_Weight_Mag               =o_Weight_Mag               ;   
    Weight.o_Weight_Wdg               =o_Weight_Wdg               ;   
    Weight.o_Weight_Stat_Core         =o_Weight_Stat_Core         ;
    Weight.o_Weight_Rot_Core          =o_Weight_Rot_Core          ;
    Weight.Weight_Shaft               =Weight_Shaft               ;
    Weight.Weight_Act_with_Shaft      =Weight_Act_with_Shaft      ;
    Weight.Weight_Total_Housing_Total =Weight_Total_Housing_Total ;
    

    % Calculate the total active mass without the shaft

    Weight.Total_Motor_Unit_Mass = Weight.Weight_Act_with_Shaft - Weight.Weight_Shaft;
    
    % Calculate the total motor unit mass (excluding drive unit) in kg using sum function
    Weight.o_Weight_Act = sum([Weight.o_Weight_Mag, Weight.o_Weight_Wdg,Weight.o_Weight_Stat_Core, Weight.o_Weight_Rot_Core]); 

end
