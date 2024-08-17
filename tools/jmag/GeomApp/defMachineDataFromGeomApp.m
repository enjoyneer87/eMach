function MachineData=defMachineDataFromGeomApp(RotorAssemRegionTable,StatorGeomArcTable,runnerType)
% function maxEndVertexTableTheta = findMaxEndVertexTableTheta(RotorAssemRegionTable)
maxEndVertexTableTheta = -Inf; % Initialize with a very small value
for regionIndex = 1:height(RotorAssemRegionTable)
    SketchList = RotorAssemRegionTable.SketchList{regionIndex};
    RotorGeomArcTable = SketchList{2};

    % Update the maximum value if the current one is larger
    if ~isempty(RotorGeomArcTable.EndVertexTabletheta)
        currentMax = max(RotorGeomArcTable.EndVertexTabletheta);
        if currentMax > maxEndVertexTableTheta
            maxEndVertexTableTheta = currentMax;
        end
    end
end
RotorOnePoleAngle=maxEndVertexTableTheta;
% end
Poles       = 360/RotorOnePoleAngle;
PhaseNumber=3;
StatorOneSlotAngle=findStatorOneSlotAngle(StatorGeomArcTable)
% NSPP
NSPP=RotorOnePoleAngle/StatorOneSlotAngle/PhaseNumber;
q=NSPP;
slots=NSPP*PhaseNumber*Poles;
%%[TF]
MachineData.Poles                 =Poles              ;   
MachineData.StatorOneSlotAngle    =StatorOneSlotAngle ;               
MachineData.PhaseNumber           =PhaseNumber        ;       
MachineData.NSPP                  =NSPP               ;   
MachineData.q                     =q                  ;
MachineData.slots                 =slots              ;   
MachineData.runnerType            =runnerType         ;
end