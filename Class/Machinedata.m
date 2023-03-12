classdef (Abstract) Machinedata
    properties
        file_name
        refFile
        file_path
        proj_path
        %Dimension

        %Winding
        torque_map
        Rs
        p 

         
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
