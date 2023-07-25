function variable = McadStatorVariable(fileName)
    variable = struct(); 
    variable.motFile=fileName;
    variable.SlotType                             =[];

    %% Axial
    variable.Stator_Lam_Length         =[]   ;                   % Stator lamination pack length
    variable.EWdg_Overhang_Rear       =[]   ;                     % End winding overhang (rear)
    variable.EWdg_Overhang_Front      =[]   ;                     %                      (front)
     
    %% Absolute 
    variable.Slot_Number                        =[]; 
    variable.Housing_Dia                        =[]; 
    variable.Stator_Lam_Dia                     =[];   
    variable.Slot_Corner_Radius                 =[];    
    variable.Tooth_Tip_Depth                    =[];     
    variable.Tooth_Tip_Angle                    =[];     
    
    %% Ratio
    variable.Ratio_Bore                         =[];

    % Type 0 
    variable.Ratio_ToothWidth                   =[];         
    variable.Ratio_SlotOpening_ParallelTooth    =[];
    variable.Ratio_SlotDepth_ParallelTooth      =[];                     
    
    % Type 1
    
    % Type 2 Parallel Slot
    % Ratio 
    variable.Ratio_SlotWidth                    =[];    
    variable.Ratio_SlotDepth_ParallelSlot       =[];            
    variable.Ratio_SlotOpening_ParallelSlot     =[];            
    
    % Type 3
    % Type 4
    % Type 5
    %%     
    variable.MinBackIronThickness               =[];
end