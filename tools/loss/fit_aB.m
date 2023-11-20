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

    [xData, yData] = prepareCurveData(B_values_min_f, W_over_f_min_f );

    % fittype과 옵션을 설정하십시오.
    % ft = fittype( 'poly7' );
    % opts = fitoptions( 'Method', 'LinearLeastSquares' );
    % opts.Normalize = 'on';
    % opts.Robust = 'LAR';
    % ft = fittype( 'rat44' );
    ft = fittype( 'rat34' );
    opts = fitoptions( 'Method', 'NonlinearLeastSquares' );
    opts.Display = 'Off';
    opts.Normalize = 'on';
    % ft = fittype('A * B^C', 'independent', 'B', 'dependent', 'W_over_f');
    % opts = fitoptions(ft);
    opts.StartPoint = [0.355579260162117 0.986171852054369 0.821476328883124 0.860910132678727 0.169553994321365 0.30740894353877 0.742527037919492 0.844867771442274];
    % opts.Lower = [0, 0];      % 하한값 설정
    % opts.Upper = [inf, inf];  % 상한값 설정
    % 데이터에 모델을 피팅하십시오.
    [fitresult, ~] = fit( xData, yData, ft, opts );

    % Perform linear regression on B_values_min_f and W_over_f_min_f
    % p = polyfit(B_values_min_f, W_over_f_min_f, 4); % 1 indicates linear fit
%% Plot
    % % Generate predicted a(B) values using the fitted model
    % B_fit = linspace(0, max(data(:, 2)), 1000);
    % 
    % % aB_fit = polyval(fitresult, B_fit);
    % aB_fit = feval(fitresult, B_fit);
    % % aB_times_f = aB_fit.* data(:, 1);
    % % bBf_times_f2 = data(:, 3) - aB_times_f;    
    % 
    % % aB = feval(fitresult, data(:, 2));
    % % scatter(data(:,2),aB);
    % 
    % % Plotting the data points and the linear regression
    % figure;
    % plot(B_values_min_f, W_over_f_min_f, 'bo', B_fit, aB_fit, 'r-');
    % xlabel('B');
    % ylabel('a(B)');
    % title('Linear Regression of a(B) for smallest f values');
    % legend('Data for smallest f', 'Linear Regression');
end
