appView=app.View();
appView.SelectEdge();
% appView.SelectByID()
curSelection=appView.GetCurrentSelection;
curSelection.IsValid;
% curSelection.NumEdges
% curSelection.SelectEdge(0)
% 
% % Rotor의 가장 바깥 Vertex잡기
% appView.SelectByPosition(78.6420,0,0,1)
% CurSelec=appView.GetCurrentSelection
% CurSelec.IsValid
% OutMostVertexId=CurSelec.VertexID(0)
% Temp

CenterAngle=22.5;
MagnetVertexId=256;
% Measurement
% x,y 잡기
% 중심 포지션이 가장 radius가 작은거 고르기 
% L1 V Angle 

% [NF]convertJmagPartStructByType중심축 Edge 목록 불러오기 (Rotor Air Barrier)
PartStructByType = convertJmagPartStructByType(PartStruct);
CenterAirPostTable=PartStructByType.CenterAirPostTable;
% 
% tolerance = 1e-5; % 허용 가능한 오차 범위 설정 (원하는 값으로 조정)
% CheckCenterAirPostTable=table();
% for rowIndex = 1:height(CenterAirPostTable)
%     isSimilar = abs(CenterAirPostTable.CentroidTheta(rowIndex) - CenterAngle) < tolerance;
%     if isSimilar
%         newRow = CenterAirPostTable(rowIndex, :);
%         % newRow.CenterRadius=AirBarrierTable.CentroidR(rowIndex);
%         CheckCenterAirPostTable=[CenterAirPostTable;newRow];
%     end
% end


%[NF] AirBiarreirTable로부터  getPositionsStructFromVertexTable :  VertexPosition 들의  radius, angle 추출 4 Theta가 22.5와 동일한 Voltex목록 생성 
for LayerIndex=1:height(CenterAirPostTable)
vertexTable=CenterAirPostTable.Vertex{LayerIndex};
VertexPosition=getPositionsStructFromVertexTable(vertexTable,app);
VertexPosition=struct2table(VertexPosition);
% 중심축에 위치하는  vertex 추출 
CenterVertexofAirBarrierTable=table();
tolerance = 1e-5; % 허용 가능한 오차 범위 설정 (원하는 값으로 조정)
for rowIndex = 1:height(VertexPosition)
        newRow = VertexPosition(rowIndex, :);
        CenterVertexofAirBarrierTable=[CenterVertexofAirBarrierTable;newRow];
        CenterVertexofAirBarrierTable.IsCenterVertex(rowIndex)=0;
end
for rowIndex = 1:height(VertexPosition)
    isSimilar = abs(VertexPosition.theta(rowIndex) - CenterAngle) < tolerance;
    if isSimilar
        CenterVertexofAirBarrierTable.IsCenterVertex(rowIndex)=1;
    end
end
CenterAirPostTable.Vertex{LayerIndex}=[CenterAirPostTable.Vertex{LayerIndex}, CenterVertexofAirBarrierTable];
end

% CenterVertexofAirBarrierTable = sortrows(CenterVertexofAirBarrierTable,"Radius","descend");
MagStruct=convertLayerMagStructFromPartStructByType(PartStructByType);
MagLayerTable=struct2table(MagStruct);
LayerTable=[MagLayerTable CenterAirPostTable];
