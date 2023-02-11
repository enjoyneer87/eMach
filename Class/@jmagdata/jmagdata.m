classdef jmagdata <emlab_MachineData
    properties
    jproj_path
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
    
%   output data name (cell)
    outputName
    end
    methods
    obj=Jmag_fcn_result_export(obj)
    obj=jmag_fcn_graph_export(obj,name) 
    end

end