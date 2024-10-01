function [elementCentersTable,NonReaderlementConnectivity] = allocateElementConnectivity(elementCentersTable, DT)
    numElements = size(elementCentersTable, 1);  % 요소 수
    % elementCentersTable.elementConnectivity = cell(numElements, 1);  % 연결 정보를 저장할 셀 배열
%% jplotReader에 있는 요소만 추출
  jplotReaderElePosArray = [elementCentersTable.x, elementCentersTable.y];  % 두 열 배열 (x, y)
  incenterArray = DT.incenter;  % DelaunayTriangulation의 incenter (내접원의 중심)        
  pointIndexArray=DT.pointLocation(jplotReaderElePosArray);
  % elementCentersTable.elementConnectivity=DT.ConnectivityList(pointIndexArray,:);
  % NonReaderlementConnectivity=DT.ConnectivityList(~pointIndexArray,:);

end