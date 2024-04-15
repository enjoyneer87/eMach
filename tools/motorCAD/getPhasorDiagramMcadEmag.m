function ResultMotorcadEmagPhasorDiagram                      = getPhasorDiagramMcadEmag(mcad)
    % From motorcadResultPhasorDiagram method
    % UNTITLED2 Summary of this function goes here
    % Detailed explanation goes here
    
    % Initialize the struct for storing results
    ResultMotorcadEmagPhasorDiagram                      = struct();
    
    % Retrieve various variables from Motor-CAD using the GetVariable method
    [~,ResultMotorcadEmagPhasorDiagram.DCBusVoltage                ]      = mcad.GetVariable('DCBusVoltage');
    [~,ResultMotorcadEmagPhasorDiagram.PoleNumber                  ]      = mcad.GetVariable('Pole_Number');
    [~,ResultMotorcadEmagPhasorDiagram.PhaseVoltage                ]      = mcad.GetVariable('PhaseVoltage');
    [~,ResultMotorcadEmagPhasorDiagram.ShaftSpeed                  ]    = mcad.GetVariable('ShaftSpeed');
    [~,ResultMotorcadEmagPhasorDiagram.RmsBackEMFPhase             ]         = mcad.GetVariable('RmsBackEMFPhase');
    [~,ResultMotorcadEmagPhasorDiagram.RMSPhaseResistiveVoltage_D  ]                    = mcad.GetVariable('RMSPhaseResistiveVoltage_D');
    [~,ResultMotorcadEmagPhasorDiagram.RMSPhaseResistiveVoltage_Q  ]                    = mcad.GetVariable('RMSPhaseResistiveVoltage_Q');
    [~,ResultMotorcadEmagPhasorDiagram.RMSPhaseResistiveVoltage    ]                  = mcad.GetVariable('RMSPhaseResistiveVoltage');
    [~,ResultMotorcadEmagPhasorDiagram.RMSPhaseReactiveVoltage_D   ]                   = mcad.GetVariable('RMSPhaseReactiveVoltage_D');
    [~,ResultMotorcadEmagPhasorDiagram.RMSPhaseReactiveVoltage_Q   ]                   = mcad.GetVariable('RMSPhaseReactiveVoltage_Q');
    [~,ResultMotorcadEmagPhasorDiagram.PhasorRMSPhaseVoltage       ]               = mcad.GetVariable('PhasorRmsPhaseVoltage');
    [~,ResultMotorcadEmagPhasorDiagram.PhasorLoadAngle             ]         = mcad.GetVariable('PhasorLoadAngle');
    [~,ResultMotorcadEmagPhasorDiagram.PhasorPowerFactorAngle      ]                = mcad.GetVariable('PhasorPowerFactorAngle');
    [~,ResultMotorcadEmagPhasorDiagram.PhaseAdvance                ]      = mcad.GetVariable('PhaseAdvance');
    [~,ResultMotorcadEmagPhasorDiagram.RMSPhaseCurrent             ]         = mcad.GetVariable('RMSPhaseCurrent');
    [~,ResultMotorcadEmagPhasorDiagram.RMSPhaseCurrent_D           ]           = mcad.GetVariable('RMSPhaseCurrent_D');
    [~,ResultMotorcadEmagPhasorDiagram.RMSPhaseCurrent_Q           ]           = mcad.GetVariable('RMSPhaseCurrent_Q');
    [~,ResultMotorcadEmagPhasorDiagram.FluxLinkageLoad             ]         = mcad.GetVariable('FluxLinkageLoad');
    [~,ResultMotorcadEmagPhasorDiagram.FluxLinkageLoad_D           ]           = mcad.GetVariable('FluxLinkageLoad_D');
    [~,ResultMotorcadEmagPhasorDiagram.FluxLinkageLoad_Q           ]           = mcad.GetVariable('FluxLinkageLoad_Q');
    [~,ResultMotorcadEmagPhasorDiagram.FluxLinkageQAxisCurrent_D   ]                   = mcad.GetVariable('FluxLinkageQAxisCurrent_D');
    [~,ResultMotorcadEmagPhasorDiagram.InductanceDxCurrent_D       ]               = mcad.GetVariable('InductanceCurrent_D');
    [~,ResultMotorcadEmagPhasorDiagram.InductanceQxCurrent_Q       ]               = mcad.GetVariable('InductanceCurrent_Q');
    
    % Additional variables if necessary
    % e.g., ResultMotorcadEmagPhasorDiagram.AdditionalVariable                      = mcad.GetVariable('AdditionalVariableName');
    
end
