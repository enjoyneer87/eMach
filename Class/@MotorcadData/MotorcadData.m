classdef MotorcadData <emlab_MachineData
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
    
%% phasor diagram tap
    phasorDiagram
%% Lab
    ModelParameters_MotorLAB
    

    end
    methods
        obj=rawPsiDataPost(obj)
    end
%     methods (Static)
%         obj.phasorDiagram=motorcadResultPhasorDiagram(obj)
%     end

%     methods (Static)
%         obj.file_path=MotorcadData.motorcadMotPath
%     end
end

