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
        
        force_map
        Material
        SampleNumber
        Stress
        Strain
        Modulus
        %     Power Rating
        Vdc
        Vs_max
        Is_max
        % LUT 
        LUT

        %Force 

        %Mechanical
    end

        
end
