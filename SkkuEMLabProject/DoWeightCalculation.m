function DoWeightCalculation(mcad)

mcad.DoWeightCalculation()                                              % Weight calculation
[~, o_Weight_Mag       ]= mcad.GetVariable("Weight_Calc_Magnet")      ; % Magnet's mass 
[~, o_Weight_Wdg       ]= mcad.GetVariable("Weight_Calc_Copper_Total"); % Winding's mass 
[~, o_Weight_Stat_Core ]= mcad.GetVariable("Weight_Calc_Stator_Lam")  ; % Stator core's mass  
[~, o_Weight_Rot_Core  ]= mcad.GetVariable("Weight_Calc_Rotor_Lam")   ; % Rotor core's mass
[~, Weight_Shaft       ]= mcad.GetVariable("Weight_Shaft_Active")     ; % Shaft's mass  
[~, Weight_Act         ]= mcad.GetVariable("Weight_Calc_Total")       ; % Active mass
[o_Weight_Act          ]= Weight_Act - Weight_Shaft                   ; % Shaft's mass retrieved

%% 45 kg motor, rest of drvie unit 50kg
o_Weight_Mag+o_Weight_Wdg+o_Weight_Stat_Core+o_Weight_Rot_Core+Weight_Shaft