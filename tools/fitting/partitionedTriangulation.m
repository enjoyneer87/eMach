function triangulations = partitionedTriangulation(WireTable)
    % partitionedTriangulation - slotIndex별로 구분된 삼각분할을 수행
    %
    % 입력:
    %   WireTable - 파트별 x, y 좌표가 담긴 테이블
    %
    % 출력:
    %   triangulations - 각 파트별로 구분된 델로네 삼각분할 객체를 담은 셀 배열
    
    % 각 slotIndex에 대해 삼각분할을 수행할 삼각분할 객체를 저장할 셀 배열
    triangulations = {};
    
    % slotIndex의 개수 확인
    numSlots = length(WireTable.TtileTableByElerow);
    
    for slotIndex = 1:numSlots
        % 현재 slotIndex에 해당하는 x, y 좌표 가져오기
        x = [WireTable.TtileTableByElerow{slotIndex}.x];
        y = [WireTable.TtileTableByElerow{slotIndex}.y];
        
        % 삼각분할을 수행하여 결과를 저장
        triangulations{slotIndex} = delaunayTriangulation(x, y);
    end
    
    % 결과 출력
    disp('삼각분할이 완료되었습니다.');
end