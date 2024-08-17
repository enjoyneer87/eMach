function fitresult=fit_aBSigmoid(data)
    % 데이터에서 각각의 f, B, W 값을 추출합니다.
    f_values = data(:, 1);
    B_values = data(:, 2);
    W_values = data(:, 3);

    % 각 행마다 W/f 값을 계산합니다.
    W_over_f = W_values ./ f_values;

    % f의 최솟값을 가진 행을 추출합니다.
    min_f = min(f_values);
    min_f_rows = data(abs(f_values - min_f) < 1e-10, :); % 부동 소수점 비교를 위한 작은 허용치 사용
    B_values_min_f = min_f_rows(:, 2);
    W_over_f_min_f = W_over_f(abs(f_values - min_f) < 1e-10);

    [xData, yData] = prepareCurveData(B_values_min_f, W_over_f_min_f );

    % 시그모이드 형태의 함수로 피팅합니다.
    ft = fittype('A/(1 + exp(-(B-B0)/C))', 'independent', 'B', 'dependent', 'W_over_f');
    opts = fitoptions(ft);
    % 시작점, 하한, 상한을 설정합니다.
    opts.StartPoint = [max(W_over_f_min_f), median(B_values_min_f), 0.1];
    % opts.Lower = [0, min(B_values_min_f), 0];
    % opts.Upper = [max(W_over_f_min_f), max(B_values_min_f), inf];
    % 
    %     ft = fittype('A * B^C', 'independent', 'B', 'dependent', 'W_over_f');
    % opts = fitoptions(ft);
    % opts.StartPoint = [1, 2];  % 시작점 설정
    % opts.Lower = [0, 0];      % 하한값 설정
    % opts.Upper = [inf, inf];  % 상한값 설정
    % 데이터에 모델을 적용하여 피팅합니다.
    [fitresult, ~] = fit(xData, yData, ft, opts);

    % 피팅 결과를 사용하여 a(B) 값을 예측합니다.
    B_fit = linspace(0, max(B_values), 1000);
    aB_fit = feval(fitresult, B_fit);
    % aB_times_f = aB_fit.* f_values;
    % bBf_times_f2 = W_values - aB_times_f;    

    % 데이터 포인트와 회귀선을 그립니다.
    figure;
    plot(B_values_min_f, W_over_f_min_f, 'bo', B_fit, aB_fit, 'r-');
    xlabel('B');
    ylabel('a(B)');
    title('최소 f 값에 대한 a(B)의 회귀분석');
    legend('최소 f의 데이터', '회귀분석');
end
