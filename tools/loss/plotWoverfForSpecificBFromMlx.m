function plotWoverfForSpecificB(tableData, B_value)
    data=table2array(tableData);
    B_fit = linspace(0, max(data(:, 2)), 1000);

    %% Get a(B) fitting model
    aB_fitmodel = fit_aB(data);
    
    %% Get b(B,f) fitting model
    bBf_fitmodel = fit_bBf(data);

    %% Calculate a(B)*f and b(B,f)*f^2 for the given data
    aB = feval(aB_fitmodel, B_value) ;
    bBf_times_f = feval(bBf_fitmodel, B_value, data(:, 1)) .* (data(:, 1));

     %% Calculate the predicted W values based on a(B)*f and b(B,f)*f^2
    W_f = aB + bBf_times_f;
    % figure
    scatter(data(:, 1), W_f,'b');
    hold on
    scatter(data(:, 1), aB, 'k');

end