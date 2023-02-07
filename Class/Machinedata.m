classdef (Abstract) Machinedata
    properties
        %Dimension

        %Winding
        torque_map
        Rs
        p 
        file_name
        file_path
        jmag_version 
        %Material
        %EM
        flux_linkage
        current
        beta
        voltage
        rpm
        %Simulation File
        
        force
        Material
        SampleNumber
        Stress
        Strain
        Modulus
        %     Power Rating
        Vdc
        Vs_max
        Is_max
        
        % Map
        LUT

        %Force 

        %Mechanical
    end
    methods 
    function Machinedata=Machinedata(p)
        Machinedata.p=p;
    end
    end

        
end
