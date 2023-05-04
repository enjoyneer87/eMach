classdef FEASimulJmag < FEASimul
    properties
        jmag_file_name
        file_path
        jmag_version  
    end
    methods 
        function obj=FEASimulJmag(Input)
            if isempty(obj.file_name)==1    
                obj.jmag_file_name= Input.file_name;
                obj.jmag_version = Input.jmag_version;
            elseif isempty(obj.file_name)==0 &  obj.file_name==Input.file_name
                obj.jmag_version = Input.jmag_version;
            elseif isempty(obj.file_name)==0 & obj.file_name~=Input.file_name
                obj.jmag_file_name= Input.file_name;
                obj.jmag_version = Input.jmag_version;
                disp('file_name_changed')
            end
        end
    end

     
end