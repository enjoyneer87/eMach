classdef (Abstract) ResultData
    %UNTITLED4 Summary of this class goes here
    %   아마도 시뮬레이션의 결과 (single인지 OP, multi인지 불분명)

    properties
        Property1
        p
    end

    methods
%         function obj = ResultData(inputArg1,inputArg2)
%             %UNTITLED4 Construct an instance of this class
%             %   Detailed explanation goes here
%             obj.Property1 = inputArg1 + inputArg2;
%         end

        function outputArg = method1(obj,inputArg)
            %METHOD1 Summary of this method goes here
            %   Detailed explanation goes here
            outputArg = obj.Property1 + inputArg;
        end
        function ResultData=ResultData(p)
            ResultData.p=p
        end
    end
end