function comparison_results = compare3dDatasets(X1, Y1, Z1, X2, Y2, Z2)
    % X, Y 값 범위를 일치시키기 위한 보간
    X = linspace(min([min(X1), min(X2)]), max([max(X1), max(X2)]), 1000);
    Y = linspace(min([min(Y1), min(Y2)]), max([max(Y1), max(Y2)]), 1000);
    [Xgrid, Ygrid] = meshgrid(X, Y);

    % Z 데이터셋 보간
    Z1_interp = griddata(X1, Y1, Z1, Xgrid, Ygrid, 'cubic');
    Z2_interp = griddata(X2, Y2, Z2, Xgrid, Ygrid, 'cubic');

    % 절대 오차 계산
    absolute_error = abs(Z1_interp - Z2_interp);
    max_absolute_error = max(absolute_error(:));
    min_absolute_error = min(absolute_error(:));

    % 상대 오차 계산
    relative_error = abs((Z1_interp - Z2_interp) ./ Z1_interp);
    max_relative_error = max(relative_error(:));
    min_relative_error = min(relative_error(:));

    % RMSE 계산
    rmse = sqrt(mean((Z1_interp(:) - Z2_interp(:)).^2));

    % 상대 오차 surface 생성
    relative_error_surface = abs((Z1_interp - Z2_interp) ./ Z1_interp);

    % 결과를 구조체에 저장
    comparison_results.max_absolute_error = max_absolute_error;
    comparison_results.min_absolute_error = min_absolute_error;
    comparison_results.max_relative_error = max_relative_error;
    comparison_results.min_relative_error = min_relative_error;
    comparison_results.rmse = rmse;
    comparison_results.relative_error_surface = relative_error_surface;

    % 상대 오차 surface 출력
    figure;
    surf(Xgrid, Ygrid, relative_error_surface);
    title('상대 오차 Surface');
    xlabel('X');
    ylabel('Y');
    zlabel('상대 오차');
end
