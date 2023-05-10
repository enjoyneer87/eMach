classdef ResultMotorcadEmagData < ResultMotorcadData
    %UNTITLED7 Summary of this class goes here
    %   Detailed explanation goes here

    properties
        xgraphDataS=struct()
        graphNumber
    end

    methods
        %% 생성자 메서드
        function obj = ResultMotorcadEmagData(motorcadDataObj)
            % ResultMotorcadLabData의 생성자
            % ResultMotorcadData 객체의 속성 전체를 상속받아 obj의 속성으로 설정
            obj = obj@ResultMotorcadData(motorcadDataObj);
        end
        
        %% Export and Plot Pointseries Data
%         function obj = exportPlotGraph(obj,setGraphName)
%             % setGraphName define externally
%             % setGraphName should be cell array format
%             % eg) setGraphName=acceptVariableNumInputs('BackEMFLineToLine12');
% 
%             mcad = actxserver('MotorCAD.AppAutomation');
%             %% MagneticGraphPoint
%             PointsPerCycle=120
%             NumberCycles=1
%             obj.xgraphDataS.graphNames=setGraphName;
%             graphNumber=length(setGraphName);
%             obj.graphNumber=graphNumber;
%     
%             NumGraphPoints = (PointsPerCycle * NumberCycles) + 1;
%             RotorPosition = zeros(NumGraphPoints, 1);
%             valueforGraph = zeros(NumGraphPoints, 1);
%             for dataIndex = 1:graphNumber
%             
%                 for loop = 0:NumGraphPoints-1
%                 [success,x,y] = mcad.GetMagneticGraphPoint(setGraphName{dataIndex}, loop);
%                 
%                     if success == 0
%                         RotorPosition(loop+1) = x;
%                         valueforGraph(loop+1) = y;
%                     end
%                 end
% 
%                 obj.xgraphDataS.valueforGraph{dataIndex}=valueforGraph;
%                 figure(1);
%                 plot(RotorPosition, valueforGraph);
%                 %title(setGraphName{dataIndex});
%                 xlabel('Rotor Position (EDeg)');
%                 ylabel(setGraphName{dataIndex});
%                 hold on
%     
%             %% GetMagnetic3DGraphPoint(seriesName, sliceNumber, pointNumber, timeStepNumber, xValue, yValue)
%     
%             %% GetPowerGraphPoint(seriesName, pointNumber, xValue, yValue)
%             
%     
%             %% GetTemperatureGraphPoint(seriesName, pointNumber, xValue, yValue)
%     
%             end
%         end
%         
        function exportObjectToMat(obj, filename)
         save(filename, string(obj));
        end
        %%
    end  
end