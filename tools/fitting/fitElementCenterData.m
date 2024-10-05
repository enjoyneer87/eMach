function fitresult= fitElementCenterData(ElementCenterValueArray,ElementCenterX,ElementCenterY,YesPlot)
    % biharmonicinterp 방식으로 보간 모델 생성
    fitresult = fit([ElementCenterX, ElementCenterY], ElementCenterValueArray, 'biharmonicinterp');
    %% plot 
    if nargin>3
    scatter3(ElementCenterX,ElementCenterY,ElementCenterValueArray,'MarkerEdgeColor','flat')
    hold on
    plot(fitresult);
    centerAllFigures   
    end
end
