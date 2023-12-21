function InnerMostConductorEdgeTable=findInnerMostConductorEdgeTable(PartStruct)
    tolerance=1e-5;
    isConductor=contains({PartStruct.Name},'Conductor');
    conductorStruct=PartStruct(isConductor);
    clear isConductor
    [~,index] = sortrows([conductorStruct.CentroidR].', "descend");
    conductorStruct = conductorStruct(index);    
    clear index
    OutMostConductorStruct=conductorStruct(1);

    % Select Edge
    % Start and End Vertex Position is Max  
    [startPosition,StartPosIndex]=sort(OutMostConductorStruct.Edge.startPosition(:,4),"descend");
    [endPosition,EndPosIndex]=sort(OutMostConductorStruct.Edge.endPosition(:,4),"descend");
    if StartPosIndex(1)==EndPosIndex(1) && startPosition(1)-endPosition(1)<tolerance
        InnerMostConductorEdgeTable=OutMostConductorStruct.Edge(EndPosIndex(1),:);
    end

    %% Conductor  길이정보
    InnerMostConductorEdgeTable.Width=norm(InnerMostConductorEdgeTable.startPosition(1:2)-InnerMostConductorEdgeTable.endPosition(1:2));
    % length=struct()

    length=[];
    for Edgeindex=1:height(OutMostConductorStruct.Edge)
    length(Edgeindex)=norm(OutMostConductorStruct.Edge.startPosition(Edgeindex,1:2)-OutMostConductorStruct.Edge.endPosition(Edgeindex,1:2));
    end
    conductorDimension=uniquetol(length);
    InnerMostConductorEdgeTable.conductorDimension=conductorDimension;
    InnerMostConductorEdgeTable.ConductorID=OutMostConductorStruct.partIndex;
    InnerMostConductorEdgeTable.ConductorName=OutMostConductorStruct.Name;

end