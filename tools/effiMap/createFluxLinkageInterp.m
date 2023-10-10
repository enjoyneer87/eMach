function  [fitresult, gof,statics]=createFluxLinkageInterp(originDqTable,ValidationDqTable)
    if isvarofTable(originDqTable,'FluxLinkageD')
    [xData, yData, zData] = prepareSurfaceData( originDqTable.Id_Peak, originDqTable.Iq_Peak, originDqTable.FluxLinkageD );
    elseif isvarofTable(originDqTable,'Flux_Linkage_D')
    [xData, yData, zData] = prepareSurfaceData( originDqTable.Id_Peak, originDqTable.Iq_Peak, originDqTable.Flux_Linkage_D );
    end

    % fittype과 옵션을 설정하십시오.
    ft = 'cubicinterp';
    opts = fitoptions( 'Method', 'CubicSplineInterpolant' );
    opts.ExtrapolationMethod = 'linear';
    opts.Normalize = 'on';
    [fitresult, gof] = fit( [xData, yData], zData, ft, opts );
    % 검증 데이터와 비교하십시오.

    if isvarofTable(ValidationDqTable,'FluxLinkageD')
    [xValidation, yValidation, zValidation] = prepareSurfaceData(ValidationDqTable.Id_Peak,ValidationDqTable.Iq_Peak,ValidationDqTable.FluxLinkageD );
    elseif isvarofTable(ValidationDqTable,'Flux_Linkage_D')
    [xValidation, yValidation, zValidation] = prepareSurfaceData(ValidationDqTable.Id_Peak,ValidationDqTable.Iq_Peak,ValidationDqTable.Flux_Linkage_D );
    end

    residual = zValidation - fitresult( xValidation, yValidation );
    statics.nNaN = nnz( isnan( residual ) );
    residual(isnan( residual )) = [];
    statics.sse = norm( residual )^2;
    statics.rmse = sqrt( statics.sse/length( residual ) );
    fprintf( '''%s'' 피팅에 대한 검증의 적합도:\n', 'FluxLinkage' );
    fprintf( '    SSE : %f\n', statics.sse );
    fprintf( '    RMSE : %f\n', statics.rmse );
    fprintf( '    데이터 영역 밖에 %i개의 점이 있습니다.\n', statics.nNaN );


    
    % 플롯에 대한 Figure를 생성하십시오.
    figure( 'Name', 'FluxLinkage' );
    
    % 좌표축 제한을 계산하십시오.
    xlim = [min( [xData; xValidation] ), max( [xData; xValidation] )];
    ylim = [min( [yData; yValidation] ), max( [yData; yValidation] )];
    
    % 데이터의 피팅을 플로팅하십시오.
    figure(1)
    h = plot( fitresult, [xData, yData], zData, 'XLim', xlim, 'YLim', ylim );
    % 플롯에 검증 데이터를 추가하십시오.
    hold on
    h(end+1) = plot3( xValidation, yValidation, zValidation, 'bo', 'MarkerFaceColor', 'w' );
    hold off
    firsutInputName=originDqTable.Properties.Description;
    ValidinputName= ValidationDqTable.Properties.Description;
    legend( h, 'FluxLinkage Interpolation Surface', [firsutInputName,'FluxlinkageD vs. Id, Iq'], [ValidinputName,' FluxlinkageD vs. Id, Iq'], 'Location', 'NorthEast', 'Interpreter', 'none' );
    % 좌표축에 레이블을 지정하십시오.
    xlabel( 'Id', 'Interpreter', 'none' );
    ylabel( 'Iq', 'Interpreter', 'none' );
    zlabel( 'FluxlinkageD', 'Interpreter', 'none' );
    grid on
    % view( -0.3, 90.0 );
    formatter_sci
    % 잔차 플로팅.
    figure(2)
    % h = plot( fitresult, [xData, yData], zData, 'Style', 'Residual', 'XLim', xlim, 'YLim', ylim );
    % 플롯에 검증 데이터를 추가하십시오.
    hold on
    h(end+1) = plot3( xValidation, yValidation, zValidation - fitresult( xValidation, yValidation ), 'bo', 'MarkerFaceColor', 'w' );
    hold off
    legend( h, [firsutInputName,'FluxLinkage - residual'], ['FluxLinkage',ValidinputName,'residual'], 'Location', 'NorthEast', 'Interpreter', 'none' );
    % 좌표축에 레이블을 지정하십시오.
    xlabel( 'Id', 'Interpreter', 'none' );
    ylabel( 'Iq', 'Interpreter', 'none' );
    zlabel( 'FluxlinkageD', 'Interpreter', 'none' );
    grid on
    % view( -0.3, 90.0 );
    formatter_sci
    % 등고선 플롯을 만드십시오.
    figure(3)
    h = plot( fitresult, [xData, yData], zData, 'Style', 'Contour', 'XLim', xlim, 'YLim', ylim );
    % 플롯에 검증 데이터를 추가하십시오.
    hold on
    h(end+1) = plot( xValidation, yValidation, 'bo', 'MarkerFaceColor', 'w' );
    hold off
    legend( h, 'FluxLinkage Interpolation Surface', [firsutInputName,'FluxlinkageD vs. Id, Iq'], [ValidinputName,'FluxlinkageD vs. Id, Iq'], 'Location', 'NorthEast', 'Interpreter', 'none' );
    % 좌표축에 레이블을 지정하십시오.
    xlabel( 'Id', 'Interpreter', 'none' );
    ylabel( 'Iq', 'Interpreter', 'none' );
    grid on
    formatter_sci
end