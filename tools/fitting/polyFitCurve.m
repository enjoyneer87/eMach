function [fitresult, gof] = polyFitCurve(xData, yData, degree)
    % polyFitCurve - xData, yData에 대해 다항식 곡선을 피팅
    %
    % 사용법:
    % [fitresult, gof] = polyFitCurve(xData, yData, degree)
    %
    % 입력:
    %   xData: 피팅할 x 값들 (1D 배열)
    %   yData: 피팅할 y 값들 (1D 배열)
    %   degree: 다항식 차수 (예: 2는 2차 다항식)
    %
    % 출력:
    %   fitresult: 피팅된 모델 (예: 다항식 모델)
    %   gof: 피팅의 적합성 정보 (Goodness-of-fit)
    
    % 다항식 피팅 유형 설정
    ft = fittype(['poly' num2str(degree)]);
    
    % 피팅 옵션 설정 (필요시 수정 가능)
    fitOptions = fitoptions('Method', 'LinearLeastSquares');
    
    % 데이터 피팅
    [fitresult, gof] = fit(xData(:), yData(:), ft, fitOptions);
    
    % 결과 그래프 플롯
    figure('Name', 'Curve Fitting');
    plot(fitresult, xData, yData);
    title(['Polynomial Fit (Degree = ' num2str(degree) ')']);
    xlabel('X Data');
    ylabel('Y Data');
    grid on;
end