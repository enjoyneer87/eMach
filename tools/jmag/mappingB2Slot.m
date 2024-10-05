function curWireTable=mappingB2Slot(DataStruct,curWireTable)

%% dev
% DataStruct=load('e10MS_ConductorModel_REF_Load~16_Case28_MagB.mat')
% curWireTable=refWireTableBackup
%% def Data
FielNameCurDSTR=fieldnames(DataStruct);
DataName=strsplit(FielNameCurDSTR{end},'_');
DataName=DataName{1};
%%  get All Element Table By Slot   [JplotReader Unit은 [m]]
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

%% get All Node Table
AllNodeTable=array2table(DataStruct.nodes);
AllNodeTable.Properties.VariableNames={'id','x','y','z'};
if isempty(AllNodeTable.Properties.VariableUnits)
    AllNodeTable.Properties.VariableUnits={'id','mm','mm','mm'};
    AllNodeTable.x=m2mm(AllNodeTable.x);
    AllNodeTable.y=m2mm(AllNodeTable.y);
    AllNodeTable.z=m2mm(AllNodeTable.z);
end

%%  Field data aggregation (combine all DataIndex fields)
%  properties 
fieldNamesJReader = fieldnames(DataStruct);
Boolvalue2Get = contains(fieldNamesJReader, DataName, "IgnoreCase", true);
DataNameList = fieldNamesJReader(Boolvalue2Get);
NumTimeStep = length(DataNameList);

if istable(curWireTable)
    WireIndexList = curWireTable.partIndex;
    for Partindex = 1:length(WireIndexList)
        WireIndex = WireIndexList(Partindex);
        elementCentersTable             = AllelementCentersTable(AllelementCentersTable.partId==WireIndex,:);    
        curWireTable.DT{Partindex}=delaunayTriangulation(curWireTable.DT{Partindex}.Points);
        %%  elementCentersTable
        curWireTable.elementCentersTable{Partindex} = elementCentersTable;
    end
     %% DataType Assign
    if contains(DataName, 'force', 'IgnoreCase', true) || contains(DataName, 'MagA', 'IgnoreCase', true)
        DataType = 'Node';    
    else
        DataType = 'Element';
    end

    %% Aggregate all FieldPerStep data for this PartIndex
    combinedData = struct('xReal', [], 'xImg', [], 'yReal', [], 'yImg', [], 'zReal', [], 'zImg', []);
    for DataIndex = 1:NumTimeStep
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
        
    %%  Make VarName List By id(Node or Element)
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
            boolId=ismember(JplotReaderTabvarNames,PartEleIdsCell);
            
        else
            PartNodeIds          =curWireTable.NodeTable{Partindex}.nodes(:,1);
            PartNodeIdsStr        =num2str(PartNodeIds);
            PartNodeIdsCell       =cellstr(PartNodeIdsStr)';
            PartNodeIdsCell = strtrim(PartNodeIdsCell);

            fieldTimeTable = array2table(zeros(NumTimeStep, length(PartNodeIds)));
            fieldTimeTable.Properties.VariableNames = PartNodeIdsCell;
            boolId=ismember(JplotReaderTabvarNames,PartNodeIdsCell);
        end
        fieldxTimeTable = fieldTimeTable;
        fieldyTimeTable = fieldTimeTable;
        fieldzTimeTable = fieldTimeTable;

    %% Trim By ID
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
     %% check DT Num Element and Data NumElement 
     if strcmp(DataType,'Element') & ~width(fieldxTimeTable)==len(curWireTable.DT{Partindex}.ConnectivityList)
        nodes = curWireTable.NodeTable{Partindex}.nodes;
        CenterPoints=[curWireTable.elementCentersTable{Partindex}.x,...
                      curWireTable.elementCentersTable{Partindex}.y];
        elementConnectivityMat=findNearestNodes(1:len(nodes),nodes(:,2:3),CenterPoints,3);
        curWireTable.DT{Partindex}=triangulation(elementConnectivityMat,curWireTable.DT{Partindex}.Points);    
     end
    end   
else
    disp('table partTable needed');
end

end