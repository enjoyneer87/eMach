classdef JmagStudy < JmagModel
    %JMAGSTUDY 이 클래스의 요약 설명 위치
    %   자세한 설명 위치
    
    properties
        jmagStudyName
    end
    
    methods
        function obj = JmagStudy(inputArg1,inputArg2)
            %JMAGSTUDY 이 클래스의 인스턴스 생성
            %   자세한 설명 위치
            obj.jmagStudyName = inputArg1 + inputArg2;
        end
        
        function outputArg = method1(obj,inputArg)
            %METHOD1 이 메서드의 요약 설명 위치
            %   자세한 설명 위치
            outputArg = obj.jmagStudyName + inputArg;
        end
    end
end

