function graphData =extractGraphMotorCad(obj,setGraphName)
            % setGraphName define externally
            % setGraphName should be cell array format
        mcad = actxserver('MotorCAD.AppAutomation');
%         obj.xgraphDataS.graphNames=setGraphName;
%         obj.xgraphDataS.graphNumber=
%         setGraphName=acceptVariableNumInputs('BackEMFLineToLine12');
%% 이건 왜할려고했지?
%     if class(obj) == 'CalibrationMotorCAD'
%         obj.calibrationStudyName=setGraphName{1};
%     end
%%   
    PointsPerCycle=obj.PointsPerCycle;
    NumberCycles=obj.NumberCycles;
    if numel(setGraphName)==1
        dataIndex=1  % setGraphName should be cell array format     
        NumGraphPoints = (PointsPerCycle * NumberCycles) + 1;
        RotorPosition = zeros(NumGraphPoints, 1);
        valueforGraph = zeros(NumGraphPoints, 1);
%         for dataIndex = 1:graphNumber
        for loop = 0:NumGraphPoints-1
    %     [success,x,y] = invoke(mcad,'GetMagneticGraphPoint',setGraphName{dataIdenx}, loop);
        [success,x,y] = mcad.GetMagneticGraphPoint(setGraphName{dataIndex}, loop);    
            if success == 0
                RotorPosition(loop+1) = x;
                valueforGraph(loop+1) = y;
            end
        end
        graphData.x=RotorPosition;
        graphData.y=valueforGraph;

%         figure(1);
%         plot(RotorPosition, valueforGraph);
%         title(setGraphName{dataIndex});
%         xlabel('Rotor Position (EDeg)');
%         ylabel(setGraphName{dataIndex});
    end
        
end