
%% REF
clear interpList

for LossIndex=1:3
    for csvindex=1:height(REFTable)
    interpList{csvindex,LossIndex}.REFTable=REFTable.dqTable{csvindex}(:,[1:2,LossIndex+2]);
    interpList{csvindex,LossIndex}.SCLTable=SCLTable.dqTable{csvindex}(:,[1:2,LossIndex+2]);
    % interp REFTable
    InputTable=REFTable.dqTable{csvindex}(:,[1:2,LossIndex+2]);
    PlotName=InputTable.Properties.VariableNames{3};
    [tempFitResult, tempGof, tempSingleDataSet] = createInterpDataSetofStrWithFieldName(InputTable, PlotName);

    interpList{csvindex,LossIndex}.REFFIt     =tempFitResult;
    interpList{csvindex,LossIndex}.REFDataSet =tempSingleDataSet;
    % interp SCLTable
    InputTable=SCLTable.dqTable{csvindex}(:,[1:2,LossIndex+2])
    PlotName=InputTable.Properties.VariableNames{3};
    [tempFitResult, tempGof, tempSingleDataSet] = createInterpDataSetofStrWithFieldName(InputTable, PlotName);
    interpList{csvindex,LossIndex}.SCLFIt     =tempFitResult;
    interpList{csvindex,LossIndex}.SCLDataSet =tempSingleDataSet;
    interpList{csvindex,LossIndex}.FitName    =PlotName;
    RatioTable=SCLTable.dqTable{csvindex}(:,[1:2,LossIndex+2]);
    RatioTable.Is=RatioTable.Is/2;
    % RatioTable.Is=RatioTable.Is;

    PlotName=InputTable.Properties.VariableNames{3};
    % interp RatioTable
    [tempFitResult, tempGof, tempSingleDataSet] = createInterpDataSetofStrWithFieldName(RatioTable, PlotName);
    interpList{csvindex,LossIndex}.SCLFIt4Ratio     =tempFitResult;
    interpList{csvindex,LossIndex}.SCLDataSet4Ratio =tempSingleDataSet;
    interpList{csvindex,LossIndex}.FitName          =PlotName;
    end
end
N = 5; 
X = linspace(0,pi*3,1000);
C = linspecer(N)
colorList=num2cell(C,2)
markerList={'o','^'}
% speedList
modelIndex=1
close all
linesize=4

%% relation Ship
csvindex=2
LossIndex=3
hold on
% scatter3(xData,yData,interpList{csvindex,LossIndex}.REFFIt(xData,yData),'x')
scatter3(interpList{csvindex,LossIndex}.REFDataSet.xData,interpList{csvindex,LossIndex}.REFDataSet.yData,interpList{csvindex,LossIndex}.REFDataSet.zData)
hold on
scatter3(interpList{csvindex,LossIndex}.REFDataSet.xData,interpList{csvindex,LossIndex}.REFDataSet.yData,interpList{csvindex,LossIndex}.REFDataSet.zData)
close all
% plot(interpList{csvindex,LossIndex}.REFFIt)
%% DEF SCLREF Ratio
for csvindex=1:height(REFTable)-1
    figure(1)
    xData=interpList{csvindex,LossIndex}.SCLDataSet4Ratio.xData;
    yData=interpList{csvindex,LossIndex}.SCLDataSet4Ratio.yData;
    SCLREFRatio=interpList{csvindex,LossIndex}.SCLFIt4Ratio(xData,yData)./interpList{csvindex,LossIndex}.REFFIt(xData,yData);
    zData=SCLREFRatio;
    xData4Box(:,csvindex)=xData;
    yData4Box(:,csvindex)=yData;
    zData4Box(:,csvindex)=zData;
    scatter3(xData,yData,SCLREFRatio,'Marker','*','LineWidth',5,'MarkerEdgeColor',colorList{csvindex},'DisplayName',[num2str(speedList(csvindex)),'k[RPM]']);
    hold on
    ft='thinplate';
    % CubicSplineInterpolant
    opts = fitoptions('Method', 'thinplate');
    % opts = fitoptions('Method', 'CubicSplineInterpolant');
    % opts.ExtrapolationMethod = 'linear';
    % opts = fitoptions('Method', 'BiharmonicInterpolant');
    % opts = fitoptions('Method', 'NonlinearLeastSquares');
    opts.ExtrapolationMethod = 'auto';   
    zData=SCLREFRatio;
    [interpList{csvindex,LossIndex}.Ratiofitresult, gof] = fit([xData, yData], zData, ft, opts);
    % plot(interpList{csvindex,LossIndex}.Ratiofitresult);
end
hold on
% plot3DBoxPlot(zData4Box', xData', yData')
boxplot3D(zData4Box, xData, yData)
for csvindex=1:height(REFTable)-1
    figure(1)
    hold on
    xData=interpList{csvindex,LossIndex}.SCLDataSet4Ratio.xData;
    yData=interpList{csvindex,LossIndex}.SCLDataSet4Ratio.yData;
    SCLREFRatio=interpList{csvindex,LossIndex}.SCLFIt4Ratio(xData,yData)./interpList{csvindex,LossIndex}.REFFIt(xData,yData);
     text(xData,yData*1.01,SCLREFRatio,num2str(csvindex),"FontSize",20,"BackgroundColor",color_code(255))

end

legend
setlegendBoxShape(4)
trimLegendToIndex(5)

% savefig(figure(1),'SClREFRatio_Map.fig')
close all
%% Merge Model
% for LossIndex=1:3
modelIndex=1
csvindex=4
for csvindex=1:height(REFTable)-1
    %% REF 
    figure(modelIndex+1)
    plot(interpList{csvindex,LossIndex}.REFFIt)
    hold on
    scatter3(interpList{csvindex,LossIndex}.REFDataSet.xData,interpList{csvindex,LossIndex}.REFDataSet.yData,interpList{csvindex,LossIndex}.REFDataSet.zData,'Marker',markerList{1},'LineWidth',linesize,'MarkerFaceColor',colorList{csvindex},'MarkerEdgeColor',colorList{csvindex},'DisplayName',[num2str(speedList(csvindex)),'k[RPM]'])
    grid on
    legend
    setlegendBoxShape(4)
    formatterFigure4Paper('double','2x2')
    %% SCL
    figure(modelIndex+2)
    plot(interpList{csvindex,LossIndex}.SCLFIt)
    hold on
    scatter3(interpList{csvindex,LossIndex}.SCLDataSet.xData,interpList{csvindex,LossIndex}.SCLDataSet.yData,interpList{csvindex,LossIndex}.SCLDataSet.zData,'Marker',markerList{2},'LineWidth',linesize,'MarkerFaceColor',colorList{csvindex},'MarkerEdgeColor',colorList{csvindex},'DisplayName',[num2str(speedList(csvindex)),'k[RPM]'])
    for i=1:2
    markerObjects = findobj(figure(modelIndex+i), 'Type', 'Axes');
    % for axindex=1:3
    markerObjects.ZLabel.String='Loss[kW]'
    markerObjects.XLabel.String='I d,pk [A]'
    markerObjects.YLabel.String='I q,pk [A]'
    end
    grid on
    legend
    setlegendBoxShape(4)
    formatterFigure4Paper('double','2x2')
end
% end

%% Per Speed
for csvindex=1:height(REFTable)-1
    %% REF 
    figure(csvindex+modelIndex+3)
    plot(interpList{csvindex,LossIndex}.REFFIt)
    hold on
    scatter3(interpList{csvindex,LossIndex}.REFDataSet.xData,interpList{csvindex,LossIndex}.REFDataSet.yData,interpList{csvindex,LossIndex}.REFDataSet.zData,'Marker',markerList{1},'LineWidth',linesize,'MarkerFaceColor',colorList{csvindex},'MarkerEdgeColor',colorList{csvindex},'DisplayName',['REF: ',num2str(speedList(csvindex)),'k[RPM]'])
    %% SCL
    plot(interpList{csvindex,LossIndex}.SCLFIt)
    hold on
    scatter3(interpList{csvindex,LossIndex}.SCLDataSet.xData,interpList{csvindex,LossIndex}.SCLDataSet.yData,interpList{csvindex,LossIndex}.SCLDataSet.zData,'Marker',markerList{2},'LineWidth',linesize,'MarkerEdgeColor',colorList{csvindex},'DisplayName',['SCL ',num2str(speedList(csvindex)),'k[RPM]'])
    markerObjects = findobj(figure(csvindex+modelIndex+3), 'Type', 'Axes');
    % for axindex=1:3
    markerObjects.ZLabel.String='Loss[kW]'
    markerObjects.XLabel.String='I d,pk [A]'
    markerObjects.YLabel.String='I q,pk [A]'
    grid on
    legend
    setlegendBoxShape(4)
    formatterFigure4Paper('double','2x2')
end 

fitresults=[]
for rpmIndex=1:5
fitresults=[fitresults;{interpList{rpmIndex,3}.SCLFIt}] 
end

% devFitSurft4D
%%