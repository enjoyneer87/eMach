classdef MotorcadData <emlab_MachineData
    % Proj - MotorcadProj
    % Model - MotorcadModel
    % Study - MotorcadData
    % Result - Model by Result or Study by Result or any
    properties
%% 
    motorcadMotPath
    motocadLabPath
    matfileFindList
%%
    I1=struct('unit','A')
    I2=struct('unit','A')
    I3=struct('unit','A')
    Iabc=table() %one period
    FFT_Iabc=table()
%%  
    u1=struct()
    u2=struct()  
    u3=struct()
    FFT_uabc=table()
%%     u3=-u1-u2
   
    fluxlink_1=struct()
    fluxlink_2=struct()  
    fluxlink_3=struct()
    FFT_fluxlinkabc=table()

%%   Thermal
    ArmatureConductor_Temperature
    Magnet_Temperature
    Shaft_Temperature
    Bearing_Temperature_R
    Bearing_Temperature_F
    Airgap_Temperature

%%   ModelParameters_MotorLAB
    TwindingCalc_MotorLAB
    TmagnetCalc_MotorLAB
    RotorWindingTemp_Calc_Lab
    RotorWindingTemp_Ref_Lab
    tempOrigin
    tempOriginFile

    elec_torque
    shaft_torque
%% emag
    OpenCircuitCalc =1
    MagneticSolver =1
    ProximityLossModel =1
    HybridACLossMethod =1
    LabModel_ACLoss_Method =1
    StackingFactor_Magnetics =1
    solver =struct()
    multiplier =struct()
    stackingFactor =struct()
    calcMethod =struct()
    manufacturingInfo = struct()
%% phasor diagram tap
    phasorDiagram
%% Lab
    ModelParameters_MotorLAB
    LossParameters_MotorLAB
%% OPTIMIZATION VARIABLE RANGE
    OPTIMIZATION= struct()


    

    end
    methods
        obj=rawPsiDataPost(obj)
        obj=exportRawLossMap(obj)
    end
%     methods (Static)
%         obj.phasorDiagram=motorcadResultPhasorDiagram(obj)
%     end

%     methods (Static)
%         obj.file_path=MotorcadData.motorcadMotPath
%     end
end

