function DT=plotTriangulationWithValues(WireTable,DataName,slotIndex, stepNumber)
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
    %%
    values = WireTable.(DataName){slotIndex}.(sprintf('Step%d', stepNumber));  
    % 좌표 가져오기
    x = [WireTable.(DataName){slotIndex}.x];
    y = [WireTable.(DataName){slotIndex}.y];
    % z = zeros(size(x));  % z 좌표가 없는 경우 평면으로 가정
    % 삼각분할
    DT = delaunayTriangulation(x, y);
    % % 삼각형 메쉬 내의 더 조밀한 그리드 생성
    % [Xq, Yq] = meshgrid(linspace(min(x), max(x), 50), linspace(min(y), max(y), 50));
    % % 물리량을 보간 (interpolation)
    % interpolatedValues = griddata(x, y, values, Xq, Yq, 'cubic');
    % % interpolatedValues에서 NaN 값을 제외
    % validIdx = ~isnan(interpolatedValues);

    % % 유효한 Xq, Yq, 그리고 interpolatedValues만 선택
    % XqValid = Xq(validIdx);
    % YqValid = Yq(validIdx);
    % 보간된 데이터를 통해 부드러운 표면 그리기
    % surf(Xq, Yq, interpolatedValues, 'EdgeColor', 'none');
    % fitResult = fitFielddataxy(Xq, Yq, interpolatedValues);
    % iosr.figures.cmrMap

    % title(sprintf('Smooth Step %d Values Visualization', stepNumber));

    % % 삼각형의 중심 좌표 계산
    % IC = incenter(DT);
    % 
    % % trisurf를 이용해 물리량을 중심에 할당하여 시각화
    % trisurf(DT.ConnectivityList, x, y, z, values, 'EdgeColor', 'none');
    % interpolatedValue=getdeluayInterpPointValue(177,12,values,DT)
    % colorbar;
    % title(sprintf('Step %d Values Visualization', stepNumber));
    % 
    % 삼각형 중심에 zData를 할당하여 시각화
    % hold on;
    % patch('Faces', DT.ConnectivityList, 'Vertices', [IC, z'], ...
    %       'FaceVertexCData', values', 'FaceColor', 'flat', 'EdgeColor', 'none');
    % 
    % hold off;
end