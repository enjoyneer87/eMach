function interpolatedValue=getdeluayInterpPointValue(px,py,values,DT)
% % 보간할 포인트 좌표 (예: px, py)
% %% dev
% % px=pxr
% % py=pyr
% % DT=WireFitTable.DT{slotIndex}
% % [a,b]=getMinMax(DT.Points(:,1))
% % [a,b]=getMinMax(DT.Points(:,2))
% % values=Brvalues
% queryPoints = [px, py];
% % 쿼리 포인트가 어느 삼각형에 속하는지 확인
% triangleID = pointLocation(DT, queryPoints);
% 
% % 해당 삼각형의 정점 좌표 가져오기
% triVerts = DT.ConnectivityList(triangleID, :);
% 
% % 삼각형의 정점 좌표
% triCoords = DT.Points(triVerts, :);
% 
% % 
% % x=DT.Points(:,1)
% % y=DT.Points(:,2)
% % z = zeros(size(x));  % z 좌표가 없는 경우 평면으로 가정
% 
% % trisurf(DT.ConnectivityList, x, y, z, values, 'EdgeColor', 'none')
% % 보간할 포인트에 대한 중점 좌표 계산
% baryCoords = cartesianToBarycentric(DT, triangleID, queryPoints);
% 
% % 보간된 값을 계산
%     interpolatedValue=zeros(height(baryCoords),1);
%     for pointIdx=1:height(baryCoords)
%      interpolatedValue(pointIdx,1) = dot(baryCoords(pointIdx,:), values(triVerts(pointIdx,:)));
%     end

% function interpolatedValue = getdeluayInterpPointValue(px, py, values, DT)
    % 보간할 포인트 좌표
    queryPoints = [px, py];
    
    % 쿼리 포인트가 속하는 삼각형 찾기
    triangleID = pointLocation(DT, queryPoints);
    
    % 삼각형 정점 좌표 가져오기
    triVerts = DT.ConnectivityList(triangleID, :);
    
    % 삼각형의 정점 좌표
    triCoords = DT.Points(triVerts, :);
    
    % 보간할 포인트에 대한 중점 좌표 계산
    baryCoords = cartesianToBarycentric(DT, triangleID, queryPoints);
    
    % 각 포인트에 대한 보간된 값 계산
    interpolatedValue = sum(baryCoords .* values(triVerts), 2);
end

