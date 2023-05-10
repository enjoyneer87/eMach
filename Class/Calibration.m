classdef  (Abstract) Calibration 
    %CALIBRATION 이 클래스의 요약 설명 위치
    %   자세한 설명 위치
    
    properties
        calibrationStudyName
        calibrationVar
        refVar
        calibrationObjectName
        calibrationObjectRefData
        calibratedSolution
    end
    
    methods
        function obj = Calibration(calibrationStudyName, calibrationObjectName, calibrationObjectRefData, var, varRefValue)
            %CALIBRATION 이 클래스의 인스턴스 생성
            %   자세한 설명 위치
            
            % 입력 인수 누락 시 경고 메시지 출력
            if nargin < 2
                warning('calibrationVar 입력이 누락되었습니다. 빈 배열을 할당합니다.');
                var = [];
            end
            if nargin < 3
                warning('varRefValue입력이 누락되었습니다. 빈 배열을 할당합니다.');
                varRefValue = [];
            end
            if nargin < 4
                warning('calibrationObject 입력이 누락되었습니다. 빈 배열을 할당합니다.');
                calibrationObject = [];
            end
            
%             % 클래스 변수 count 초기화
%             persistent count
%             if isempty(count)
%                 count = 0;
%             end
%             
%             % count 변수 증가 및 객체 이름 생성
%             count = count + 1;
%             objName = ['Calibration_', num2str(count)];
            
            % 객체 속성 초기화
            obj.calibrationStudyName = calibrationStudyName;
            obj.calibrationVar = var;
            obj.refVar = varRefValue;
            obj.calibrationObjectRefData = calibrationObjectRefData;
            obj.calibrationObjectName = calibrationObjectName;
            obj.calibratedSolution = [];
            
            % 객체 이름 할당
%             assignin('base', objName, obj);
        end
    end
end