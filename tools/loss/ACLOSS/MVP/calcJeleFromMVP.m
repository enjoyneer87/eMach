function [JeleTimeTable,JnodeTable] = calcJeleFromMVP(MVPTimeTable,elementCentersTable,timeStep)
    % dev
    % timeStep=endtime/120
    % timeStep=endtime/onePeriodSteps
    % MVPTimeTable=WireStruct(SlotIndex).MVPTimeTable;
    % elementCentersTable=WireStruct(SlotIndex).elementCentersTable
    % Node
    % NodeIds=WireStruct(SlotIndex).NodeTable.NodeID;
    % NodeIds=NodeTable.NodeID;
    % NodeIdStr=num2str(NodeIds);
    % MVPTimeTable     =array2table(zeros(NumTimeStep,length(NodeIdStr)));
    % MVPTimeTable.Properties.VariableNames=cellstr(NodeIdStr);  
    %% MVP > JNodeEddy > JeleEddy
    MVP = MVPTimeTable.Variables;
    Jnode      =calcJnodeEddyFromMVP(MVP,timeStep);
    JnodeTable =array2table(Jnode);
    NodeIdcell =MVPTimeTable.Properties.VariableNames;
    JnodeTable.Properties.VariableNames=NodeIdcell;
    JeleTimeTable =  calcJeleFromJNodes(elementCentersTable, JnodeTable);
    
end
