function PartStruct=mappingB2Slot(DataStruct,PartStruct)

%% dev

% DataStruct=load('e10MS_ConductorModel_REF_Load~16_Case28_MagB.mat')
FielNameCurDSTR=fieldnames(DataStruct);
DataName=strsplit(FielNameCurDSTR{end},'_');
DataName=DataName{1};
% PartStruct=WireTable

% PartStruct=refWireTableBackup;
% DataStruct=FieldResult{caseIndex}
    %% cart2 pol
    %[tb unit allocate]
    

  %% By Slot - Load와 noload 동일하다고 가정 [JplotReader Unit은  [m]]
    AllelementCentersTable=array2table(DataStruct.element_centers);
    AllelementCentersTable.Properties.VariableNames={'id', 'partId', 'eleType', 'x', 'y', 'z', 'area'};
    if isempty(AllelementCentersTable.Properties.VariableUnits)
        % disp('단위 확인필요합니다 일단은 mm로 할당합니다')
        AllelementCentersTable.Properties.VariableUnits={'id','partId','eleType','mm','mm','mm','mm^2'};
                AllelementCentersTable.x=m2mm(AllelementCentersTable.x);
                AllelementCentersTable.y=m2mm(AllelementCentersTable.y);
                AllelementCentersTable.area=msq2mmsq(AllelementCentersTable.area);
    else
        if ~any(contains(AllelementCentersTable.Properties.VariableUnits,'mm'))
                AllelementCentersTable.x=m2mm(AllelementCentersTable.x);
                AllelementCentersTable.y=m2mm(AllelementCentersTable.y);
                AllelementCentersTable.area=msq2mmsq(AllelementCentersTable.area);

        end
    end
     %%  Node Table
     % scatter(AllNodeTable.x,AllNodeTable.y)
    AllNodeTable=array2table(DataStruct.nodes);
    AllNodeTable.Properties.VariableNames={'id','x','y','z'};
    if isempty(AllNodeTable.Properties.VariableUnits)
    AllNodeTable.Properties.VariableUnits={'id','mm','mm','mm'};
    AllNodeTable.x=m2mm(AllNodeTable.x);
    AllNodeTable.y=m2mm(AllNodeTable.y);
    AllNodeTable.z=m2mm(AllNodeTable.z);
    end

    % 
    % DT=delaunayTriangulation([AllNodeTable.x,AllNodeTable.y]);
    % % BShape=boundaryshape(DT)
    % % triplot(DT)
    % QueryelementIDs=DT.pointLocation(AllelementCentersTable.x,AllelementCentersTable.y);
    % QuieryConnect=DT.ConnectivityList(QueryelementIDs,:);
%% 
if istable(PartStruct)
    WireIndexList=PartStruct.partIndex;
    for Partindex=1:len(WireIndexList)
        WireIndex=WireIndexList(Partindex);

        % end
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
        if contains(DataName,'force','IgnoreCase',true)||contains(DataName,'MagA','IgnoreCase',true)
            fieldTimeTable     =array2table(zeros(NumTimeStep,length(NodeIds)));
            fieldTimeTable.Properties.VariableNames=cellstr(NodeIdStr); 
            fieldTimeTable.Properties.Description='Nodal';
            DataType='Node';
        else
            DataType='Element';
            fieldTimeTable     =array2table(zeros(NumTimeStep,length(EleIds)));
            fieldTimeTable.Properties.VariableNames=cellstr(EleIdsStr);  
            fieldTimeTable.Properties.Description='element';
        end
        elementCentersTable          = AllelementCentersTable(AllelementCentersTable.partId==WireIndex,:);
        [elementCentersTablewConnect,NonReaderlementConnectivity]      = allocateElementConnectivity(elementCentersTable, PartStruct.DT{Partindex});
        PartStruct.DT{Partindex}=triangulation(elementCentersTablewConnect.elementConnectivity,PartStruct.DT{Partindex}.Points);
        PartStruct.elementCentersTable{Partindex} = elementCentersTablewConnect;
        fieldxTimeTable    =fieldTimeTable;
        fieldyTimeTable    =fieldTimeTable;
        fieldzTimeTable    =fieldTimeTable;
        %% time or Freq
        for DataIndex=1:NumTimeStep
                FieldPerStep     =array2table(DataStruct.(MagANameList{DataIndex}));
                if width(FieldPerStep)==4||strcmp(DataType,'Node')
                    FieldPerStep.Properties.VariableNames(1:4)={'id','x','y','z'};
                    if strcmp(DataType,'Element')
                    % matchingIndice =findMatchingRow(FieldPerStep.id,EleIds);
                    boolId=ismember(FieldPerStep.id,EleIds);
                    else
                    % matchingIndice =findMatchingRow(FieldPerStep.id,NodeIds);
                    boolId=ismember(FieldPerStep.id,NodeIds);
                    end
                    fieldxTimeTable(DataIndex,:).Variables=FieldPerStep.x(boolId,:)';
                    fieldyTimeTable(DataIndex,:).Variables=FieldPerStep.y(boolId,:)';
                    fieldzTimeTable(DataIndex,:).Variables=FieldPerStep.z(boolId,:)';
                elseif width(FieldPerStep)==7 
                    FieldPerStep.Properties.VariableNames={'id','xReal','xImg','yReal','yImg','zReal','zImg'};
                    if strcmp(DataType,'Element')
                    % matchingIndice =findMatchingRow(FieldPerStep.id,EleIds);
                    boolId=ismember(FieldPerStep.id,EleIds);
                    else
                    % boolId =findMatchingRow(FieldPerStep.id,NodeIds);
                    boolId=ismember(FieldPerStep.id,NodeIds);

                    end
                    fieldxTimeTable(DataIndex,:).Variables=complex(FieldPerStep.xReal(boolId,:)',FieldPerStep.xImg(boolId,:)'); 
                    fieldyTimeTable(DataIndex,:).Variables=complex(FieldPerStep.yReal(boolId,:)',FieldPerStep.yImg(boolId,:)'); 
                    fieldzTimeTable(DataIndex,:).Variables=complex(FieldPerStep.zReal(boolId,:)',FieldPerStep.zImg(boolId,:)'); 
               end
        end
        %% 2 PartStruct(Table)
        PartStruct.fieldxTimeTable{Partindex}=fieldxTimeTable;
        PartStruct.fieldyTimeTable{Partindex}=fieldyTimeTable;   
        PartStruct.fieldzTimeTable{Partindex}=fieldzTimeTable;   
    end
else 
    disp('table partTable needed')
end


end
