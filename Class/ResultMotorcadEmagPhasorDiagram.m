classdef ResultMotorcadEmagPhasorDiagram < ResultMotorcadEmagData
    %UNTITLED9 Summary of this class goes here
    %   Detailed explanation goes here

    properties
        ShaftSpeed
        RMSBackEMFPhase
        RMSPhaseResistiveVoltage_D
        RMSPhaseResistiveVoltage_Q
        RMSPhaseResistiveVoltage
        RMSPhaseReactiveVoltage_D
        RMSPhaseReactiveVoltage_Q
        PhasorRMSPhaseVoltage
%       RmsPhaseDriveVoltage - % The required rms Phase Voltage at the output of the drive taking into account sine filter
        PhaseVoltage
        PhasorLoadAngle
        PhasorPowerFactorAngle

        PhaseAdvance
        RMSPhaseCurrent
        RMSPhaseCurrent_D
        RMSPhaseCurrent_Q

        FluxLinkageLoad
        FluxLinkageLoad_D
        FluxLinkageLoad_Q
        FluxLinkageQAxisCurrent_D
        InductanceXCurrent_D
        InductanceXCurrent_Q

    end

    methods

        function outputArg = method1(obj,inputArg)
            %METHOD1 Summary of this method goes here
            %   Detailed explanation goes here
            outputArg = obj.Property1 + inputArg;
        end
    end
end