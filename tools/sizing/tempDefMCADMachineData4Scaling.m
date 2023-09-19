function MachineData=tempDefMCADMachineData4Scaling(mcad)
    %% 
    [~,MachineData.Pole_Number]                                =mcad.GetVariable('Pole_Number'       );
    [~,MachineData.Slot_Number]                                =mcad.GetVariable('Slot_Number'       );
    [~,MachineData.DCBusVoltage]                               =mcad.GetVariable('DCBusVoltage'       );

    MachineData.Slot_Number=double(MachineData.Slot_Number);
    MachineData.Pole_Number=double(MachineData.Pole_Number);
    %% Geometry
    [~,MachineData.Stator_Lam_Dia               ]              =mcad.GetVariable('Stator_Lam_Dia'       );
    [~,MachineData.Stator_Lam_Length            ]              =mcad.GetVariable('Stator_Lam_Length'    );    
    [~,MachineData.Motor_Length]                               =mcad.GetVariable('Motor_Length');
    [~,MachineData.Housing_Dia]                                =mcad.GetVariable('Housing_Dia');
    %% Winding
    [~,MachineData.Area_Slot]                                   =mcad.GetVariable('Area_Slot'    );    
    [~,MachineData.ParallelPaths                ]              =mcad.GetVariable('ParallelPaths'        );
    
    MachineData.Area_Slot  =str2double(MachineData.Area_Slot);
    MachineData.ParallelPaths=double(MachineData.ParallelPaths);
    [~,MachineData.Armature_CoilStyle]                         =mcad.GetVariable('Armature_CoilStyle'    );    
    
    if double(MachineData.Armature_CoilStyle)==1
    disp('HairPin')
    [~,MachineData.WindingLayers            ]              =mcad.GetVariable('WindingLayers'    ); 
    [~,MachineData.HairpinWindingPatternMethod]            =mcad.GetVariable('HairpinWindingPatternMethod'    ); 
    MachineData.WindingLayers =double(MachineData.WindingLayers);
    [~,MachineData.Copper_Width]            =mcad.GetVariable('Copper_Width'    ); 
    [~,MachineData.Copper_Height]            =mcad.GetVariable('Copper_Height'    );    
    
    elseif double(MachineData.Armature_CoilStyle)==0
    disp('환선')
    [~,MachineData.MagTurnsConductor            ]              =mcad.GetVariable('MagTurnsConductor'    ); 
    MachineData.MagTurnsConductor =double(MachineData.MagTurnsConductor);

    end

    % [~,MachineData.GrossSlotFillFactor_IM1PH    ]            =mcad.GetVariable('GrossSlotFillFactor_IM1PH'        );
    [~,MachineData.GrossSlotFillFactor    ]                    =mcad.GetVariable('GrossSlotFillFactor'        );
    [~,MachineData.RMSCurrent]                                 =mcad.GetVariable('RMSCurrent');
    [~,MachineData.ArmatureConductorCSA]                       =mcad.GetVariable('ArmatureConductorCSA');
    [~,MachineData.NumberStrandsHand ]                         =mcad.GetVariable('NumberStrandsHand');

    MachineData.RMSCurrentDensity =calcCurrentDensity(MachineData.RMSCurrent,double(MachineData.ParallelPaths),double(MachineData.NumberStrandsHand),MachineData.ArmatureConductorCSA);

    %% 상세 치수 (Rotor)
    RefRotorVariable = McadRotorVariable('');
    RefRotorVariable=getMcadVariable(RefRotorVariable,mcad);    
    MachineData=mergeStructs(MachineData,RefRotorVariable);  % 기존에꺼 중복되면 앞에껄로 합칠껄
    %% 상세 치수 (Stator)
    RefStatorVariable = McadStatorVariable('');
    RefStatorVariable=getMcadVariable(RefStatorVariable,mcad);
    MachineData=mergeStructs(MachineData,RefStatorVariable);  % 기존에꺼 중복되면 앞에껄로 합칠껄
    %%
    
    %% Winding Loss
    [~,MachineData.ResistanceEndWinding         ]              =mcad.GetVariable('EndWindingResistance_Lab');
    [~,MachineData.EndWindingInductance_Lab     ]              =mcad.GetVariable('EndWindingInductance_Lab');    
    [~,MachineData.ArmatureConductor_Temperature]              =mcad.GetVariable('ArmatureConductor_Temperature');      %
    [~,MachineData.Resistance_MotorLAB          ]              =mcad.GetVariable('Resistance_MotorLAB');
    [~,MachineData.ACConductorLossProportion_Lab]              =mcad.GetVariable('ACConductorLossProportion_Lab');
    [~,MachineData.NumberOfCuboids_LossModel_Lab]              =mcad.GetVariable('NumberOfCuboids_LossModel_Lab');
     
    % [~,MachineData.ArmatureWindingResistancePh]                =mcad.GetVariable('ArmatureWindingResistancePh');
    MachineData.ResistanceActivePart=MachineData.Resistance_MotorLAB-MachineData.ResistanceEndWinding;

    %% Int32 2 double

end