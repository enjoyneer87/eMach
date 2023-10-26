function p_b = fit_bBf(data)
    % data: 3-column matrix where 
    %       column 1 is f, 
    %       column 2 is B, 
    %       column 3 is W

    % Using fit_aB to get a(B)
    p_a = fit_aB(data);
    
    % Calculate a(B) * f for each row
    aB_times_f = polyval(p_a, data(:, 2)) .* data(:, 1);
    
    % Calculate W/f - a(B) * f which equals b(B, f) * f^2
    bBf_times_f2 = data(:, 3) - aB_times_f;
    
    % Perform linear regression on f^2 and bBf_times_f2
    f2 = data(:, 1).^2;
    p_b = polyfit(f2, bBf_times_f2, 1); % 1 indicates linear fit
    
    % Generate predicted b(B, f) values using the fitted model
    f2_fit = linspace(0, max(f2), 100);
    bBf_fit = polyval(p_b, f2_fit);

    % Plotting the data points and the linear regression
    figure;
    plot(f2, bBf_times_f2, 'bo', f2_fit, bBf_fit, 'r-');
    xlabel('f^2');
    ylabel('b(B,f) * f^2');
    title('Linear Regression of b(B,f) for given data');
    legend('Data', 'Linear Regression');

    return;
end
