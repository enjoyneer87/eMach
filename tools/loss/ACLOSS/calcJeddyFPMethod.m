function WireStruct=calcJeddyFPMethod(DataStruct,WireStruct,endtime)

    %% By Slot - Load와 noload 동일하다고 가정
    AllelementCentersTable=array2table(DataStruct.element_centers);
    AllelementCentersTable.Properties.VariableNames={'id', 'partId', 'eleType', 'x', 'y', 'z', 'area'};
    
    for SlotIndex=1:length(WireStruct)
        WireIndex=WireStruct(SlotIndex).partIndex;
        elementCentersTable          = AllelementCentersTable(AllelementCentersTable.partId==WireIndex,:);
        elementCentersTable.Properties.VariableNames={'id', 'partId', 'eleType', 'x', 'y', 'z', 'area'};
        elementCentersTablewConnect      = calcElementConnectivity(elementCentersTable, WireStruct(SlotIndex).NodeTable);
        WireStruct(SlotIndex).elementCentersTable = elementCentersTablewConnect;
    end
    
    
    %% MVP A Field Time Table per Slot
    % Bool Mag A Table
    value2Get='MagA';
    fieldNamesJReader   =fieldnames(DataStruct);
    Boolvalue2Get       =contains(fieldNamesJReader,value2Get,"IgnoreCase",true);
    MagANameList        =fieldNamesJReader(Boolvalue2Get);
    NumTimeStep         =length(find(Boolvalue2Get));
    % init Time Table
    for SlotIndex=1:length(WireStruct)
        NodeIds          =WireStruct(SlotIndex).NodeTable.NodeID;
        NodeIdStr        =num2str(NodeIds);
        % init MVPTimeTable
        MVPTimeTable     =array2table(zeros(NumTimeStep,length(NodeIdStr)));
        MVPTimeTable.Properties.VariableNames=cellstr(NodeIdStr);  
        for DataIndex=1:NumTimeStep
            MVPperStep     =array2table(DataStruct.(MagANameList{DataIndex}));
            MVPperStep.Properties.VariableNames={'id','x','y','z'};
            matchingIndice =findMatchingRow(MVPperStep.id,NodeIds);
            MVP      =MVPperStep.z(matchingIndice,:);
            MVPTimeTable(DataIndex,:).Variables=MVP';
        end
        WireStruct(SlotIndex).MVPTimeTable=MVPTimeTable;
    end
    
    %% Jelec
    for SlotIndex=1:length(WireStruct)
        [WireStruct(SlotIndex).JeleTimeTable,WireStruct(SlotIndex).JnodeTable] = calcJeleFromMVP(WireStruct(SlotIndex).MVPTimeTable,WireStruct(SlotIndex).elementCentersTable,endtime/120);
    end

end