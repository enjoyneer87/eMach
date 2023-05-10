classdef measureddata < emlab_MachineData
    properties
    %
    I1=struct('unit','A')
    I2=struct('unit','A')
    I3=struct('unit','A')
    Iabc=table()
    FFT_Iabc=table()
    FFT_Idq=table()
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

    %%Thermal Data
    tempRise struct
    end


    methods
        dq_phasor_diagram(obj)
    end
    

end