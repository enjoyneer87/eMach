classdef MotorcadData <emlab_MachineData
    properties
    motorcadMotPath
    motocadLabPath
    matfileFindList
    I1=struct('unit','A')
    I2=struct('unit','A')
    I3=struct('unit','A')
    Iabc=table() %one period
    FFT_Iabc=table()
%     I3=-I1-I2
    u1=struct()
    u2=struct()  
    u3=struct()
    FFT_uabc=table()
    
%     u3=-u1-u2
   
    fluxlink_1=struct()
    fluxlink_2=struct()  
    fluxlink_3=struct()
    FFT_fluxlinkabc=table()

    elec_torque
    shaft_torque
    %emag
    

    %Lab
    ModelParameters_MotorLAB
    
    %phasor diagram tap
    phasorDiagram
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

