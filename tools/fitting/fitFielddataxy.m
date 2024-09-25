function fitResult = fitFielddataxy(Xq, Yq, interpolatedValues)
    % 데이터에서 NaN 제거 (보간 과정에서 NaN이 생길 수 있음)
    validIdx = ~isnan(interpolatedValues);
    xValid = Xq(validIdx);
    yValid = Yq(validIdx);
    valuesValid = interpolatedValues(validIdx);
    
    % 2차 다항식 피팅
    [fitResult, gof] = fit([xValid, yValid], valuesValid, 'poly22');
    
    % % 피팅된 값을 기반으로 새로운 표면 계산
    % fittedSurface = fitResult(Xq, Yq);
    % 
    % % 피팅 결과 출력
    % figure;
    % surf(Xq, Yq, fittedSurface);
    % title('Fitted Surface');
    % xlabel('X');
    % ylabel('Y');
    % zlabel('Fitted Values');
    % colorbar;
end