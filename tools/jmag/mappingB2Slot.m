function curWireTable=mappingB2Slot(DataStruct,curWireTable)

%% dev

% DataStruct=load('e10MS_ConductorModel_REF_Load~16_Case28_MagB.mat')
FielNameCurDSTR=fieldnames(DataStruct);
DataName=strsplit(FielNameCurDSTR{end},'_');
DataName=DataName{1};
% curWireTable=refWireTableBackup
%% By Slot - Load와 noload 동일하다고 가정 [JplotReader Unit은 [m]]
AllelementCentersTable=array2table(DataStruct.element_centers);
AllelementCentersTable.Properties.VariableNames={'id', 'partId', 'eleType', 'x', 'y', 'z', 'area'};
if isempty(AllelementCentersTable.Properties.VariableUnits)
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

%% Node Table
AllNodeTable=array2table(DataStruct.nodes);
AllNodeTable.Properties.VariableNames={'id','x','y','z'};
if isempty(AllNodeTable.Properties.VariableUnits)
    AllNodeTable.Properties.VariableUnits={'id','mm','mm','mm'};
    AllNodeTable.x=m2mm(AllNodeTable.x);
    AllNodeTable.y=m2mm(AllNodeTable.y);
    AllNodeTable.z=m2mm(AllNodeTable.z);
end

%% Field data aggregation (combine all DataIndex fields)
fieldNamesJReader = fieldnames(DataStruct);
Boolvalue2Get = contains(fieldNamesJReader, DataName, "IgnoreCase", true);
DataNameList = fieldNamesJReader(Boolvalue2Get);
NumTimeStep = length(DataNameList);

if istable(curWireTable)
    WireIndexList = curWireTable.partIndex;
    % NdeIds=[];
    % NodeCoord=[];
    % EleIds=[];
    for Partindex = 1:length(WireIndexList)
        WireIndex = WireIndexList(Partindex);
        NodeIds = [curWireTable.NodeTable{Partindex}.NodeID];
        NodeCoord = [ curWireTable.NodeTable{Partindex}.nodeCoords];
        EleIds = [curWireTable.ElementId{Partindex}];
        elementCentersTable          = AllelementCentersTable(AllelementCentersTable.partId==WireIndex,:);
        elementCentersTable           =calcElementConnectivity(elementCentersTable,NodeIds,NodeCoord);
        % [elementCentersTablewConnect,NonReaderlementConnectivity]      = allocateElementConnectivity(elementCentersTable, PartStruct.DT{Partindex});
        elementConnectivityMat=cell2matwithvaryCell(elementCentersTable.elementConnectivity);
        % if width(elementConnectivityMat)>3
            curWireTable.DT{Partindex}=delaunayTriangulation(curWireTable.DT{Partindex}.Points);
        % else
        %     curWireTable.DT{Partindex}=triangulation(elementConnectivityMat,curWireTable.DT{Partindex}.Points);
        % end
        curWireTable.elementCentersTable{Partindex} = elementCentersTable;
    end

    if contains(DataName, 'force', 'IgnoreCase', true) || contains(DataName, 'MagA', 'IgnoreCase', true)
        DataType = 'Node';    
    else
        DataType = 'Element';
    end

    % 
    % NodeIds=[];
    % NodeCoord=[];
    % EleIds=[];
    % for Partindex = 1:length(WireIndexList)
    %     WireIndex = WireIndexList(Partindex);
    %     NodeIds = [NodeIds; curWireTable.NodeTable{Partindex}.NodeID];
    %     NodeCoord = [NodeCoord; curWireTable.NodeTable{Partindex}.nodeCoords];
    %     EleIds = [EleIds; curWireTable.ElementId{Partindex}];
    % end
    % EleIdsStr        =num2str(EleIds);
    % 
    % % Initialize Time Tables
    % if contains(DataName, 'force', 'IgnoreCase', true) || contains(DataName, 'MagA', 'IgnoreCase', true)
    %     DataType = 'Node';
    %     fieldTimeTable = array2table(zeros(NumTimeStep, length(NodeIds)));
    %     fieldTimeTable.Properties.VariableNames = cellstr(num2str(NodeIds'));
    % else
    %     DataType = 'Element';
    %     fieldTimeTable = array2table(zeros(NumTimeStep, length(EleIds)));
    %     fieldTimeTable.Properties.VariableNames = cellstr((EleIdsStr));
    % end
  
    % Aggregate all FieldPerStep data for this PartIndex
    combinedData = struct('xReal', [], 'xImg', [], 'yReal', [], 'yImg', [], 'zReal', [], 'zImg', []);
    for DataIndex = 1:NumTimeStep
        % eleIDs=DataStruct.MagB_241(:,1)';
        % Fx=DataStruct.MagB_241(:,2)';
        % Fy=DataStruct.MagB_241(:,3)';
        % Fz=DataStruct.MagB_241(:,4)';

        FieldPerStep = array2table(DataStruct.(DataNameList{DataIndex}));
        if width(FieldPerStep) == 4 || strcmp(DataType, 'Node')
            FieldPerStep.Properties.VariableNames(1:4)={'id','xReal','yReal','zReal'};
            combinedData.xReal = [combinedData.xReal; FieldPerStep.xReal'];
            combinedData.yReal = [combinedData.yReal; FieldPerStep.yReal'];
            combinedData.zReal = [combinedData.zReal; FieldPerStep.zReal'];
        elseif width(FieldPerStep) == 7
            FieldPerStep.Properties.VariableNames={'id','xReal','xImg','yReal','yImg','zReal','zImg'};
            combinedData.xReal = [combinedData.xReal; FieldPerStep.xReal'];
            combinedData.xImg = [combinedData.xImg; FieldPerStep.xImg'];
            combinedData.yReal = [combinedData.yReal; FieldPerStep.yReal'];
            combinedData.yImg = [combinedData.yImg; FieldPerStep.yImg'];
            combinedData.zReal = [combinedData.zReal; FieldPerStep.zReal'];
            combinedData.zImg = [combinedData.zImg; FieldPerStep.zImg'];
        end
    end
        

      
    JplotReaderTabvarNames=num2str(FieldPerStep.id);
    JplotReaderTabvarNames=cellstr(JplotReaderTabvarNames)';
    JplotReaderTabvarNames = strtrim(JplotReaderTabvarNames);
    %% Assign data to field tables   
    

    for Partindex=1:len(WireIndexList)
        if strcmp(DataType,'Element')
            % curWireTable.partIndex       
            PartEleIds           =curWireTable.ElementId{Partindex};
            PartEleIdsStr        =num2str(PartEleIds);
            PartEleIdsCell       =cellstr(PartEleIdsStr)'; 
            PartEleIdsCell = strtrim(PartEleIdsCell);

            fieldTimeTable = array2table(zeros(NumTimeStep, length(PartEleIds)));
            fieldTimeTable.Properties.VariableNames = PartEleIdsCell;
            % matchingIndice =findMatchingRow(FieldPerStep.id,EleIds);
            boolId=ismember(JplotReaderTabvarNames,PartEleIdsCell);
            
        else
            PartNodeIds          =curWireTable.NodeTable{Partindex}.NodeID;
            PartNodeIdsStr        =num2str(PartNodeIds);
            PartNodeIdsCell       =cellstr(PartNodeIdsStr)';
            PartNodeIdsCell = strtrim(PartNodeIdsCell);

            fieldTimeTable = array2table(zeros(NumTimeStep, length(NodeIds)));
            fieldTimeTable.Properties.VariableNames = PartNodeIdsCell;
            % boolId =findMatchingRow(FieldPerStep.id,NodeIds);
            boolId=ismember(JplotReaderTabvarNames,PartNodeIdsCell);
        end
    fieldxTimeTable = fieldTimeTable;
    fieldyTimeTable = fieldTimeTable;
    fieldzTimeTable = fieldTimeTable;


     if width(FieldPerStep) == 4 || strcmp(DataType, 'Node')
        fieldxTimeTable.Variables = combinedData.xReal(:,boolId);
        fieldyTimeTable.Variables = combinedData.yReal(:,boolId);
        fieldzTimeTable.Variables = combinedData.zReal(:,boolId);
     elseif width(FieldPerStep) == 7
        fieldxTimeTable.Variables = complex(combinedData.xReal(:,boolId), combinedData.xImg(:,boolId));
        fieldyTimeTable.Variables = complex(combinedData.yReal(:,boolId), combinedData.yImg(:,boolId));
        fieldzTimeTable.Variables = complex(combinedData.zReal(:,boolId), combinedData.zImg(:,boolId));
     end  
      %% Assign results to PartStruct
      curWireTable.fieldxTimeTable{Partindex} =          fieldxTimeTable;
      curWireTable.fieldxTimeTable{Partindex}.Properties.Description=DataType;
      %
      curWireTable.fieldyTimeTable{Partindex} =          fieldyTimeTable;
      curWireTable.fieldyTimeTable{Partindex}.Properties.Description=DataType;
      %
      curWireTable.fieldzTimeTable{Partindex} =          fieldzTimeTable;
      curWireTable.fieldzTimeTable{Partindex}.Properties.Description=DataType;
    end
else
    disp('table partTable needed');
end

end