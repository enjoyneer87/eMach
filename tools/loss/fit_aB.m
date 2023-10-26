function fitresult=fit_aB(data)
    % data: 3-column matrix where 
    %       column 1 is f, 
    %       column 2 is B, 
    %       column 3 is W

    % Calculate W/f for each row
    W_over_f = data(:, 3) ./ data(:, 1);

    % Extract rows where f has its minimum value
    min_f = min(data(:, 1));
    min_f_rows = data(abs(data(:, 1) - min_f) < 1e-10, :); % Using a small tolerance for floating point equality
    B_values_min_f = min_f_rows(:, 2);
    W_over_f_min_f = W_over_f(abs(data(:, 1) - min_f) < 1e-10);

    [xData, yData] = prepareCurveData( B_values_min_f, W_over_f_min_f );

    % fittype과 옵션을 설정하십시오.
    ft = fittype( 'poly7' );
    opts = fitoptions( 'Method', 'LinearLeastSquares' );
    opts.Normalize = 'on';
    opts.Robust = 'LAR';
    
    % 데이터에 모델을 피팅하십시오.
    [fitresult, gof] = fit( xData, yData, ft, opts );

    % Perform linear regression on B_values_min_f and W_over_f_min_f
    % p = polyfit(B_values_min_f, W_over_f_min_f, 4); % 1 indicates linear fit

    % Generate predicted a(B) values using the fitted model
    B_fit = linspace(0, max(data(:, 2)), 1000);
    % aB_fit = polyval(fitresult, B_fit);
    aB_fit = feval(fitresult, B_fit);
    % Plotting the data points and the linear regression
    figure;
    plot(B_values_min_f, W_over_f_min_f, 'bo', B_fit, aB_fit, 'r-');
    xlabel('B');
    ylabel('a(B)');
    title('Linear Regression of a(B) for smallest f values');
    legend('Data for smallest f', 'Linear Regression');
end
