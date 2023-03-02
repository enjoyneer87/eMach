classdef JmagDesignTable < JmagData 
    %JMAGDESIGNTABLE 이 클래스의 요약 설명 위치
    %   자세한 설명 위치
    
    properties
        jmagDesignTable
    end
    
    methods
        function obj = getjmagDesignTable(inputArg1,inputArg2)
            %JMAGDESIGNTABLE 이 클래스의 인스턴스 생성
            %   자세한 설명 위치
            app.GetModel(u"IPM_PWM").GetStudy(u"PWM_parallel").GetDesignTable().AddCase()

            obj.Property1 = inputArg1 + inputArg2;
        end
        
        function outputArg = method1(obj,inputArg)
            %METHOD1 이 메서드의 요약 설명 위치
            %   자세한 설명 위치
            outputArg = obj.Property1 + inputArg;
        end
    end
end

