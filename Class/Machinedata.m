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

        % Object
        calibration % Calibration 객체
        optimization % Optimization 객체
        multiSimulation % MultiSimulation 객체
    end
    methods 
%     function Machinedata=Machinedata(p)
%         Machinedata.p=p;
%     end
        function obj = Machinedata(p, calibration, optimization, multiSimulation)
            obj.p = p;
            if nargin > 1
                obj.calibration = calibration;
            else
                obj.calibration = [];
            end
            if nargin > 2
                obj.optimization = optimization;
            else
                obj.optimization = [];
            end
            if nargin > 3
                obj.multiSimulation = multiSimulation;
            else
                obj.multiSimulation = [];
            end
    end
    end
        
end
