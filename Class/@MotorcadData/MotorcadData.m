classdef MotorcadData <emlab_MachineData
    properties
    proj_path
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
    %phasor diagram tap
    phasorDiagram=struct()
    end
    

end