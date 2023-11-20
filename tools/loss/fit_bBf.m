function fitModel = fit_bBf(data)
    % data: 3-column matrix where 
    %       column 1 is f, 
    %       column 2 is B, 
    %       column 3 is W
    % Using fit_aB to get a(B)
    fitresult = fit_aB(data);   
    % fitresult=fit_aBSigmoid(data);
    % Calculate a(B) * f for each row
    aB = feval(fitresult, data(:, 2));
    aB_times_f = aB.* data(:, 1);
    %%
    bBf_times_f2 = data(:, 3) - aB_times_f;    
    % Calculate b(B, f)
    bBf = bBf_times_f2 ./ (data(:, 1).^2);        
    [xData, yData, zData] = prepareSurfaceData(data(:, 2), data(:, 1), bBf);
    % Perform 2D surface fitting
    fitType = fittype('poly34');
    opts = fitoptions(fitType);
    opts.Normalize = 'on';
    fitModel = fit([xData, yData], zData, fitType,opts);
 % %%   
 %    figure;
 %    h_fit =plot(fitModel,'Style', 'Surface');
 %    hold on
 %    h_raw =scatter3(data(:, 2), data(:, 1), bBf,'DisplayName','rawData');
 %    xlabel('B');
 %    ylabel('f');
 %    zlabel('b(B,f)');
 %    % title('2D Surface Fitting of b(B,f)');
 %    legend([h_fit,h_raw] ,{'Fitted','rawData'}, 'Location', 'NorthEast', 'Interpreter', 'none');
 % 
 %    % h_fit.DisplayName = 'Fitted Surface';
 %    % h_raw.DisplayName = 'rawData';
 %    formatter_sci

    % return;
end