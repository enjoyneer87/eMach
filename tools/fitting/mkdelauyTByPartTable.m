function [DT,IC]=mkdelauyTByPartTable(WireTable,slotIndex)
    % plotTriangulationWithValues - 삼각형 중심에 물리량을 할당하여 시각화
    %
    % 입력:
    %   WireTable - 파트별 데이터가 포함된 테이블
    %   slotIndex - 시각화할 파트의 인덱스
    %   stepNumber - 물리량이 포함된 스텝 번호
    %
    % 출력:
    %   없음. 삼각형 중심에 물리량을 할당하여 시각화
    % 삼각형 중심에 할당할 물리량 가져오기     

    %% dev
    % DataName='TtileTableByElerow';
    % stepNumber=StepList
    %% Node Table
    x=    WireTable.NodeTable{slotIndex}.nodeCoords(:,1);
    y=    WireTable.NodeTable{slotIndex}.nodeCoords(:,2);
    % z = zeros(size(x));  % z 좌표가 없는 경우 평면으로 가정
    % 삼각분할
    DT = delaunayTriangulation(x, y);
    % % 삼각형의 중심 좌표 계산
    IC = incenter(DT);
end