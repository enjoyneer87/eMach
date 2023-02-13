classdef JmagData <emlab_MachineData
    properties
    jproj_path
    jmag_version ='210'
    jmagcall

    %Model
    modelName
    modelNumber
    %Study
    studyName
    studyNumber
    %Case & DesignTable
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
    obj=jmagFcnResultExport(obj)
    obj=jmagFcnGraphExport(obj,name) 

    function out=jmagCall(obj)
        obj.jmagcall=actxserver(strcat('designer.Application.',obj.jmag_version));
        out=obj.jmagcall;
%         out=obj.jmagcall
    end
    end
end