function PartStruct=getEdgeVertexIdwithXYZCheck(PartStruct,app)
   Model=app.GetCurrentModel;
   
   %% 비어있는 vertex테이블이 있을시 해당 part삭제
    deleteIndices = false(length(PartStruct), 1); % 삭제할 인덱스를 저장할 논리적 배열 초기화
    
    for partIndex = 1:length(PartStruct)
        if isempty(PartStruct(partIndex).Vertex)
            deleteIndices(partIndex) = true;
        end
    end
    
    PartStruct(deleteIndices) = []; % 한 번에 모든 빈 요소 삭제

    for   partIndex=1:length(PartStruct)
    %% get Vertex Position Function
        PositionTable=table();
        for IdIndex=1:height(PartStruct(partIndex).Vertex.VertexIds)
            VertexId=PartStruct(partIndex).Vertex.VertexIds(IdIndex);
            VertexPositionObj=Model.GetVertexPosition(VertexId);
            % cell2mat(VertexPositionObj.Value)'
            Position=[VertexPositionObj.x,VertexPositionObj.y,VertexPositionObj.z];
            [Position(5),Position(4)]=cart2pol(Position(1),Position(2),Position(3));
            Position(5)=rad2deg(Position(5));
            tempPositionTable=array2table(Position,"VariableNames",{'x','y','z','r','theta'});
            tempPositionTable = mergevars(tempPositionTable,        {'x','y','z','r','theta'}, 'NewVariableName', 'Position', 'MergeAsTable', false);
            PositionTable=[PositionTable;tempPositionTable];            
        end

        PartStruct(partIndex).Vertex=[PartStruct(partIndex).Vertex PositionTable];
      

    %% get Edge Vertex Function
        StartPosTable=table();
        MidPosTable  =table();
        EndPosable   =table();
        for IdIndex=1:height(PartStruct(partIndex).Edge.EdgeIds)
        EdgeId=PartStruct(partIndex).Edge.EdgeIds(IdIndex);
        % refObject
        RefObjEdgeStartPos      =Model.GetEdgeStartPosition(EdgeId);
        RefObjEdgeMidPos        =Model.GetEdgeMidPosition(EdgeId);
        RefObjEdgeEndPos        =Model.GetEdgeEndPosition(EdgeId);
        % Position Array   
        StartPos =cell2mat(RefObjEdgeStartPos.Value)';
        MidPos   =cell2mat(RefObjEdgeMidPos.Value)';
        EndPos   =cell2mat(RefObjEdgeEndPos.Value)';
        [StartPos(5),StartPos(4)] =cart2pol(StartPos(1),StartPos(2),StartPos(3));
        [MidPos(5),  MidPos(4)  ]   =cart2pol(MidPos(1),MidPos(2),MidPos(3));
        [EndPos(5),  EndPos(4)  ]   =cart2pol(EndPos(1),EndPos(2),EndPos(3));
        StartPos(5)=rad2deg(StartPos(5));
        MidPos(5)  =rad2deg(MidPos(5)  );
        EndPos(5)  =rad2deg(EndPos(5)  );

        % Table
        tempStartPosTable=array2table(StartPos,"VariableNames",{'x','y','z','r','theta'});
        tempMidPosTable  =array2table(MidPos  ,"VariableNames",{'x','y','z','r','theta'});
        tempEndPosable   =array2table(EndPos  ,"VariableNames",{'x','y','z','r','theta'});
        tempStartPosTable    = mergevars(tempStartPosTable, {'x','y','z','r','theta'}, 'NewVariableName', 'startPosition', 'MergeAsTable', false);
        tempMidPosTable      = mergevars(tempMidPosTable,   {'x','y','z','r','theta'}, 'NewVariableName', 'midPosition', 'MergeAsTable', false);
        tempEndPosable       = mergevars(tempEndPosable,    {'x','y','z','r','theta'}, 'NewVariableName', 'endPosition', 'MergeAsTable', false);
        % Table row
        StartPosTable=[ StartPosTable;   tempStartPosTable                        ];
        MidPosTable  =[ MidPosTable  ;   tempMidPosTable                          ];
        EndPosable   =[ EndPosable   ;   tempEndPosable                           ];
        end
    
    
    %% getEdge - VertexId with XYZCheck 
        EdgeNumber=height(PartStruct(partIndex).Edge);
    
        PartStruct(partIndex).Edge=[PartStruct(partIndex).Edge StartPosTable MidPosTable EndPosable];

        PartStruct(partIndex).Edge=addvars(PartStruct(partIndex).Edge,zeros(EdgeNumber,1),'NewVariableNames','startVertexId',Before='startPosition');
        PartStruct(partIndex).Edge=addvars(PartStruct(partIndex).Edge,zeros(EdgeNumber,1),'NewVariableNames','MidVertexId',Before='midPosition');
        PartStruct(partIndex).Edge=addvars(PartStruct(partIndex).Edge,zeros(EdgeNumber,1),'NewVariableNames','EndVertexId',Before='endPosition');
    
    
        for EdgeIndex=1:height(PartStruct(partIndex).Edge)
                matchingRowinVertexWithStartPos     = ismember(PartStruct(partIndex).Vertex.Position,   PartStruct(partIndex).Edge.startPosition(EdgeIndex,:), 'rows');
                matchingRowinVertexWithMidPos       = ismember(PartStruct(partIndex).Vertex.Position,   PartStruct(partIndex).Edge.midPosition(EdgeIndex,:) , 'rows');
                matchingRowinVertexWithEndPos       = ismember(PartStruct(partIndex).Vertex.Position,   PartStruct(partIndex).Edge.endPosition(EdgeIndex,:)  ,'rows');
                % for vertexIndex=1:Vertexnumber
                matchingVertexIndexWithStartPos  = find(matchingRowinVertexWithStartPos);
                matchingVertexIndexWithMidPos    = find(matchingRowinVertexWithMidPos);
                matchingVextexIndexWithEndPos    = find(matchingRowinVertexWithEndPos);
                if ~isempty(matchingVertexIndexWithStartPos)&&length(matchingVertexIndexWithStartPos)==1
                    PartStruct(partIndex).Edge.startVertexId(EdgeIndex)=PartStruct(partIndex).Vertex.VertexIds(matchingVertexIndexWithStartPos);
                else
                    disp('check startVertex')
                end

                if ~isempty(matchingVertexIndexWithMidPos)&&length(matchingVertexIndexWithMidPos)==1
                    PartStruct(partIndex).Edge.MidVertexId(EdgeIndex)=PartStruct(partIndex).Vertex.VertexIds(matchingVertexIndexWithMidPos);
                end

                if ~isempty(matchingVextexIndexWithEndPos)&&length(matchingVextexIndexWithEndPos)==1
                    PartStruct(partIndex).Edge.EndVertexId(EdgeIndex)=PartStruct(partIndex).Vertex.VertexIds(matchingVextexIndexWithEndPos);
                else
                    disp('check EndVertex')
                end            
        end
        % 
        % if ~isempty(PartStruct(partIndex).Vertex)
        PartStruct(partIndex).VertexMaxThetaPos=max(PartStruct(partIndex).Vertex.Position(:,5));
        PartStruct(partIndex).VertexMinThetaPos=min(PartStruct(partIndex).Vertex.Position(:,5));
        PartStruct(partIndex).VertexMaxRPos    =max(PartStruct(partIndex).Vertex.Position(:,4));
        PartStruct(partIndex).VertexMinRPos    =min(PartStruct(partIndex).Vertex.Position(:,4));
       % end
    end
% 
%     % Rotor 자석 edge 포지션 따기 
% for partIndex=1:length(PartStruct)
%     if ~isempty(PartStruct(partIndex).object.GetName) &&strcmp(PartStruct(partIndex).Name,'Magnet')
%     EdgeId=PartStruct(partIndex).Edge.EdgeIds(:)
%     % EdgePosEnd  =Model.GetEdgeEndPosition(EdgeId)
%     % EdgePosStart=Model.GetEdgeStartPosition(EdgeId)    
%     Edge=table(zeros(4,1),zeros(4,1),zeros(4,1),'VariableNames',{'x','y','z'})
%     PartStruct(partIndex).Edge=[PartStruct(partIndex).Edge Edge]    
%         for EdgeIndex=1:4
%         EdgePosMid(EdgeIndex)           =Model.GetEdgeMidPosition(EdgeId(EdgeIndex))
%         PartStruct(partIndex).Edge.x(EdgeIndex)=EdgePosMid(EdgeIndex).x
%         PartStruct(partIndex).Edge.y(EdgeIndex)=EdgePosMid(EdgeIndex).y
%         PartStruct(partIndex).Edge.z(EdgeIndex)=EdgePosMid(EdgeIndex).z
%         end
%     end
% end
end