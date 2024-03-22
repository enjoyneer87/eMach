function IronLossFrequencySeperationFitFunction(tableData)
    % 입력 데이터에서 freq, LossDensity, FluxDensity 추출
    data=table2array(tableData);
    B_fit = linspace(0, max(data(:, 2)), 1000);
    %% Get a(B) fitting model
    aB_fitmodel = fit_aB(data);
    
    %% Get b(B,f) fitting model
    bBf_fitmodel = fit_bBf(data);

    %% Calculate a(B)*f and b(B,f)*f^2 for the given data
    aB_times_f = feval(aB_fitmodel, data(:, 2)) .* data(:, 1);
    bBf_times_f2 = feval(bBf_fitmodel, data(:, 2), data(:, 1)) .* (data(:, 1).^2);

    aB = feval(aB_fitmodel, data(:, 2)) ;
    bBf_times_f = feval(bBf_fitmodel, data(:, 2), data(:, 1)) .* (data(:, 1));

    %% Calculate the predicted W values based on a(B)*f and b(B,f)*f^2
    % W_predicted = aB_times_f + bBf_times_f2;
    % W_f = aB + bBf_times_f;

    %% Plot the original W values and the predicted W values
    figure;
    
    % Original data
    scatter3(data(:, 2), data(:, 1), data(:, 3), 'filled', 'DisplayName', 'Original W data');
    hold on;


    % Predicted W values as a surface
    % B_vals = unique(data(:, 2));
    % f_vals = unique(data(:, 1));
    % 
    B_vals = linspace(min((data(:, 2))),max(data(:, 2)),100);
    f_vals = linspace(min((data(:, 1))),max(data(:, 1)),100);

    % f_vals = min(data(:,1)):50:max(data(:,1));
    [B_grid, f_grid] = meshgrid(B_vals, f_vals);
    aBf_values = arrayfun(@(B, f) feval(aB_fitmodel, B) .* f, B_grid, f_grid);
    bBfsq_values = arrayfun(@(B, f) feval(bBf_fitmodel, B, f) .* (f^2), B_grid, f_grid);
   
    aB_values = arrayfun(@(B, f) feval(aB_fitmodel, B), B_grid, f_grid);
    bBf_values = arrayfun(@(B, f) feval(bBf_fitmodel, B, f) .* (f), B_grid, f_grid);
    
    W_pred_surface = aBf_values + bBfsq_values;
    Wperfpred_surface =aB_values+bBf_values;
    a=surf(B_grid,f_grid, W_pred_surface  ,'DisplayName', 'Predicted W Surface');
    xlabel([tableData.Properties.VariableNames{2},'[',tableData.Properties.VariableUnits{2},']']);
    ylabel([tableData.Properties.VariableNames{1},'[',tableData.Properties.VariableUnits{1},']']);
    zlabel([tableData.Properties.VariableNames{3},'[',tableData.Properties.VariableUnits{3},']']);
    title('Original vs Predicted W values');  
    grid on;

    figure
    surf(B_grid,f_grid, aBf_values  ,'DisplayName', 'aBf Surface');
    figure
    surf(B_grid,f_grid, bBfsq_values  ,'DisplayName', 'aBf Surface');

    %% 
    figure
    b=surf(B_grid,f_grid, Wperfpred_surface  ,'DisplayName', 'Predicted Wf Surface');
    hold on
    scatter3(data(:, 2), data(:, 1), data(:, 3)./data(:, 1), 'filled', 'DisplayName', 'Original W data');
    % scatter3(B_grid,f_grid, aB_values  ,'DisplayName', 'Predicted Wf Surface');
    surf(B_grid,f_grid, aB_values  ,'DisplayName', 'Predicted Wf Surface');

    % c = plot(fitresult, [xData, yData], zData, 'Style', 'Contour', 'XLim', xlim, 'YLim', ylim);
     % 
    xlabel([tableData.Properties.VariableNames{2},'[',tableData.Properties.VariableUnits{2},']']);
    ylabel([tableData.Properties.VariableNames{1},'[',tableData.Properties.VariableUnits{1},']']);
    zlabel(['Wf','[W/Hz]']);
    title('Original vs Predicted Wf values');
    legend;
    grid on;
end
