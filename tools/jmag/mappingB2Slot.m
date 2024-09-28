function PartStruct=mappingB2Slot(DataStruct,PartStruct)

%% dev

% DataStruct=load('e10MS_ConductorModel_REF_Load~16_Case28_MagB.mat')
FielNameCurDSTR=fieldnames(DataStruct);
DataName=strsplit(FielNameCurDSTR{end},'_');
DataName=DataName{1};
% PartStruct=WireStruct
% PartStruct=refWireTableBackup;
% DataStruct=FieldResult{caseIndex}
  %% By Slot - Load와 noload 동일하다고 가정
    AllelementCentersTable=array2table(DataStruct.element_centers);
    AllelementCentersTable.Properties.VariableNames={'id', 'partId', 'eleType', 'x', 'y', 'z', 'area'};
if istable(PartStruct)
    WireIndexList=PartStruct.partIndex;
    for Partindex=1:len(WireIndexList)
        WireIndex=WireIndexList(Partindex);
        elementCentersTable          = AllelementCentersTable(AllelementCentersTable.partId==WireIndex,:);
        elementCentersTable.Properties.VariableNames={'id', 'partId', 'eleType', 'x', 'y', 'z', 'area'};
        % if contains(DataName,'MagA')
        elementCentersTablewConnect      = calcElementConnectivity(elementCentersTable, PartStruct.NodeTable{Partindex});
        PartStruct.connetivity{Partindex} = elementCentersTablewConnect;
        % else
        PartStruct.elementCentersTable{Partindex} = elementCentersTable;
        % end
        %% MVP A Field Time Table per Slot
        value2Get=DataName;
        fieldNamesJReader   =fieldnames(DataStruct);
        Boolvalue2Get       =contains(fieldNamesJReader,value2Get,"IgnoreCase",true);
        MagANameList        =fieldNamesJReader(Boolvalue2Get);
        NumTimeStep         =length(find(Boolvalue2Get));
        % init Time Table
        NodeIds          =PartStruct.NodeTable{Partindex}.NodeID;
        NodeIdStr        =num2str(NodeIds);
        EleIds           =PartStruct.ElementId{Partindex};
        EleIdsStr        =num2str(EleIds);
    
        % init MVPTimeTable
        fieldTimeTable     =array2table(zeros(NumTimeStep,length(EleIds)));
        fieldTimeTable.Properties.VariableNames=cellstr(EleIdsStr);  
        fieldyTimeTable    =fieldTimeTable;
        fieldxTimeTable    =fieldTimeTable;
        fieldzTimeTable    =fieldTimeTable;
        %% time or Freq
        for DataIndex=1:NumTimeStep
                FieldPerStep     =array2table(DataStruct.(MagANameList{DataIndex}));
                if width(FieldPerStep)==4
                    FieldPerStep.Properties.VariableNames={'id','x','y','z'};
                    matchingIndice =findMatchingRow(FieldPerStep.id,EleIds);
                    fieldxTimeTable(DataIndex,:).Variables=FieldPerStep.x(matchingIndice,:)';
                    fieldyTimeTable(DataIndex,:).Variables=FieldPerStep.y(matchingIndice,:)';
                    fieldzTimeTable(DataIndex,:).Variables=FieldPerStep.z(matchingIndice,:)';
                elseif width(FieldPerStep)==7
                    FieldPerStep.Properties.VariableNames={'id','xReal','xImg','yReal','yImg','zReal','zImg'};
                    matchingIndice =findMatchingRow(FieldPerStep.id,EleIds);
                    fieldxTimeTable(DataIndex,:).Variables=complex(FieldPerStep.xReal(matchingIndice,:)',FieldPerStep.xImg(matchingIndice,:)'); 
                    fieldyTimeTable(DataIndex,:).Variables=complex(FieldPerStep.yReal(matchingIndice,:)',FieldPerStep.yImg(matchingIndice,:)'); 
                    fieldzTimeTable(DataIndex,:).Variables=complex(FieldPerStep.zReal(matchingIndice,:)',FieldPerStep.zImg(matchingIndice,:)'); 
               end
        end
        %% 2 PartStruct(Table)
        PartStruct.fieldxTimeTable{Partindex}=fieldxTimeTable;
        PartStruct.fieldyTimeTable{Partindex}=fieldyTimeTable;   
        PartStruct.fieldzTimeTable{Partindex}=fieldzTimeTable;   
    end
else   
    %% element 2 PartStruct Table
    for SlotIndex=1:length(PartStruct)
        WireIndexList=PartStruct(SlotIndex).partIndex;
        elementCentersTable          = AllelementCentersTable(AllelementCentersTable.partId==WireIndexList,:);
        elementCentersTable.Properties.VariableNames={'id', 'partId', 'eleType', 'x', 'y', 'z', 'area'};
    % if contains(DataName,'MagA')
        elementCentersTablewConnect      = calcElementConnectivity(elementCentersTable, PartStruct(SlotIndex).NodeTable);
        PartStruct(SlotIndex).connetivity = elementCentersTablewConnect;
        % else
        PartStruct(SlotIndex).elementCentersTable = elementCentersTable;
        % end
    end
    %% MVP A Field Time Table per Slot
    value2Get=DataName;
    fieldNamesJReader   =fieldnames(DataStruct);
    Boolvalue2Get       =contains(fieldNamesJReader,value2Get,"IgnoreCase",true);
    MagANameList        =fieldNamesJReader(Boolvalue2Get);
    NumTimeStep         =length(find(Boolvalue2Get));
    % init Time Table
    for SlotIndex=1:length(PartStruct)
        NodeIds          =PartStruct(SlotIndex).NodeTable.NodeID;
        NodeIdStr        =num2str(NodeIds);
        EleIds           =PartStruct(SlotIndex).ElementId;
        EleIdsStr        =num2str(EleIds);

        % init MVPTimeTable
        fieldTimeTable     =array2table(zeros(NumTimeStep,length(EleIds)));
        fieldTimeTable.Properties.VariableNames=cellstr(EleIdsStr);  
        fieldyTimeTable    =fieldTimeTable;
        fieldxTimeTable    =fieldTimeTable;
        for DataIndex=1:NumTimeStep
            FieldPerStep     =array2table(DataStruct.(MagANameList{DataIndex}));
            FieldPerStep.Properties.VariableNames={'id','x','y','z'};
            matchingIndice =findMatchingRow(FieldPerStep.id,EleIds);
            Fieldx      =FieldPerStep.x(matchingIndice,:);
            Fieldy      =FieldPerStep.y(matchingIndice,:);
            fieldxTimeTable(DataIndex,:).Variables=Fieldx';
            fieldyTimeTable(DataIndex,:).Variables=Fieldy';
        end
        PartStruct(SlotIndex).fieldxTimeTable=fieldxTimeTable;
        PartStruct(SlotIndex).fieldyTimeTable=fieldyTimeTable;

    end
end


end
