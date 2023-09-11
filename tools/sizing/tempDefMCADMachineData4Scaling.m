function MachineData=tempDefMCADMachineData4Scaling(mcad)
    %% 
    [~,MachineData.Pole_Number]                                =mcad.GetVariable('Pole_Number'       );
    [~,MachineData.DCBusVoltage]                               =mcad.GetVariable('DCBusVoltage'       );

    %% Geometry
    [~,MachineData.Stator_Lam_Dia               ]              =mcad.GetVariable('Stator_Lam_Dia'       );
    [~,MachineData.Stator_Lam_Length            ]              =mcad.GetVariable('Stator_Lam_Length'    );    
    [~,MachineData.Motor_Length]                               =mcad.GetVariable('Motor_Length');
    [~,MachineData.Housing_Dia]                                =mcad.GetVariable('Housing_Dia');
    %% Winding
    [~,MachineData.MagTurnsConductor            ]              =mcad.GetVariable('MagTurnsConductor'    );    
    [~,MachineData.ParallelPaths                ]              =mcad.GetVariable('ParallelPaths'        );
    %[TB] 환선만 현재가능 
    % [~,MachineData.GrossSlotFillFactor_IM1PH    ]            =mcad.GetVariable('GrossSlotFillFactor_IM1PH'        );
    [~,MachineData.GrossSlotFillFactor    ]                    =mcad.GetVariable('GrossSlotFillFactor'        );

    %% Winding Loss
    [~,MachineData.ResistanceEndWinding         ]              =mcad.GetVariable('EndWindingResistance_Lab');
    [~,MachineData.EndWindingInductance_Lab     ]              =mcad.GetVariable('EndWindingInductance_Lab');    
    [~,MachineData.ArmatureConductor_Temperature]              =mcad.GetVariable('ArmatureConductor_Temperature');      %
    [~,MachineData.Resistance_MotorLAB          ]              =mcad.GetVariable('Resistance_MotorLAB');
    [~,MachineData.ACConductorLossProportion_Lab]              =mcad.GetVariable('ACConductorLossProportion_Lab');
    [~,MachineData.NumberOfCuboids_LossModel_Lab]              =mcad.GetVariable('NumberOfCuboids_LossModel_Lab');
     
    % [~,MachineData.ArmatureWindingResistancePh]                =mcad.GetVariable('ArmatureWindingResistancePh');
    MachineData.ResistanceActivePart=MachineData.Resistance_MotorLAB-MachineData.ResistanceEndWinding;
end