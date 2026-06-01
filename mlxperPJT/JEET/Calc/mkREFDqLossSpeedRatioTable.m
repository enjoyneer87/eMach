%% DEF REFSpeed Ratio
for csvindex=2:height(REFTable)-1
    af1=figure(2)
    af1.Name='REF Speed Incremental Ratio'
    xData=interpList{csvindex,LossIndex}.REFDataSet.xData;
    yData=interpList{csvindex,LossIndex}.REFDataSet.yData;
    SCLSpeedRatio=interpList{csvindex+1,LossIndex}.REFFIt(xData,yData)./interpList{csvindex,LossIndex}.REFFIt(xData,yData);
    zData=SCLSpeedRatio;
    xData4Box(:,csvindex)=xData;
    yData4Box(:,csvindex)=yData;
    zData4Box(:,csvindex)=zData;
    scatter3(xData,yData,SCLSpeedRatio,'Marker','*','LineWidth',5,'MarkerEdgeColor',colorList{csvindex},'DisplayName',[num2str(speedList(csvindex)),'k[RPM]']);
    hold on
    ft='thinplate';
    % CubicSplineInterpolant
    opts = fitoptions('Method', 'thinplate');
    % opts = fitoptions('Method', 'CubicSplineInterpolant');
    % opts.ExtrapolationMethod = 'linear';
    % opts = fitoptions('Method', 'BiharmonicInterpolant');
    % opts = fitoptions('Method', 'NonlinearLeastSquares');
    opts.ExtrapolationMethod = 'auto';   
    zData=SCLSpeedRatio;
    [interpList{csvindex,LossIndex}.Ratiofitresult, gof] = fit([xData, yData], zData, ft, opts);
    af=plot(interpList{csvindex,LossIndex}.Ratiofitresult);
    ax=af.Parent;
    af.FaceAlpha=csvindex/(height(REFTable)-1);
end