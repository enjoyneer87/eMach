% 
% 
% for csvindex=1:height(REFTable)
% plotMultipleInterpSatuMapSubplots(@plotFitResult,REFTable.dqTable{csvindex}(:,[1:2,LossIndex+2]));
% n=csvindex;
% close(n+1:n+3)
% end
% 
% for csvindex=1:height(SCLTable)
% plotMultipleInterpSatuMapSubplots(@plotFitResult,SCLTable.dqTable{csvindex}(:,[1:2,LossIndex+2]));
% n=csvindex;
% close(n+5:n+7)
% hold on
% end
%% REF
for csvindex=1:height(REFTable)
figure(csvindex)
InputTable=REFTable.dqTable{csvindex}(:,[1:2,LossIndex+2])
PlotName=InputTable.Properties.VariableNames{3};
[tempFitResult, tempGof, tempSingleDataSet] = createInterpDataSetofStrWithFieldName(InputTable, PlotName);
% plotFitResult(tempFitResult, tempSingleDataSet, 0);
plot(tempFitResult)
hold on
scatter3(tempSingleDataSet.xData,tempSingleDataSet.yData,tempSingleDataSet.zData,'DisplayName',PlotName)
%%
end 


for csvindex=1:height(SCLTable)
figure(csvindex+height(REFTable))
InputTable=SCLTable.dqTable{csvindex}(:,[1:2,LossIndex+2])
PlotName=InputTable.Properties.VariableNames{3};
[tempFitResult, tempGof, tempSingleDataSet] = createInterpDataSetofStrWithFieldName(InputTable, PlotName);
% plotFitResult(tempFitResult, tempSingleDataSet, 0);
plot(tempFitResult)
hold on
scatter3(tempSingleDataSet.xData,tempSingleDataSet.yData,tempSingleDataSet.zData,'DisplayName',PlotName)
%%
end 



for csvindex=1:8
    markerObjects = findobj(figure(csvindex), 'Type', 'Axes');
    % for axindex=1:3
    markerObjects.ZLabel.String='Loss[kW]'
    markerObjects.XLabel.String='I d,pk [A]'
    markerObjects.YLabel.String='I q,pk [A]'
    legend
    % end
    % formatterFigure4Paper('double','2x2')
    grid on
end



%% update Marker and displayname
colorList={'k','r','b','g'}
markerList={'o','^'}
group = ceil((1:len(CSVList)) / (len(CSVList)/2)); % 3개씩 그룹으로 할당
for csvindex=1:len(CSVList)
    cf        =figure(csvindex);
    ax        =cf.Children;
    ModelIndex=group(csvindex);
    speedIndex=csvindex-(group(csvindex)-1)*4
    curRPM    =speedList(speedIndex);
    legend([num2str(curRPM),'k','[RPM]'])
    % 모든 figure 객체 중에서 Marker 속성이 있는 객체를 찾음
    markerObjects = findobj(ax, '-property', 'Marker');
    % Marker 속성이 비어있지 않은 객체만 필터링
    markerObjects         = markerObjects(~cellfun(@isempty, get(markerObjects, 'Marker')));
    markerObjects(1).Marker=markerList{ModelIndex}
    markerObjects(1).MarkerFaceColor=colorList{speedIndex};
    % markerObjects(1).MarkerSize=12
    markerObjects(1).MarkerEdgeColor=colorList{speedIndex};
end

%% merge Figure N Model 
startNList=[1,len(CSVList)/2+1]
for nIndex=1:len(startNList)
    n=startNList(nIndex)
    figlist=[n:n+3];
    mergeFigures(figlist)   % 모델별로 합치기
    legend
    grid on
    % setlegendBoxShape(len(figlist))
    formatterFigure4Paper('double','2x2')
end

%% merge Per SPeed
startNList=[1 len(CSVList)/2+1];
for nIndex=1:len(startNList)
    figlIndexist=startNList(nIndex):startNList(nIndex)+height(SCLTable)-1;
    for indexPerIndex=1:len(figlIndexist)
        figIndex=figlIndexist(indexPerIndex);
        markerObjects = findobj(figure(figIndex), 'Type', 'line');
        for markerIndex=1:len(markerObjects)          
            if contains(markerObjects(markerIndex).Marker,markerList{1})
                markerObjects(markerIndex).DisplayName='REF'
            elseif strcmp(markerObjects(markerIndex).Marker,markerList{2})
                markerObjects(markerIndex).DisplayName='SCL'
            end
        end
    end
end
for figN=1:len(figlIndexist)
                % 모든 figure 객체 중에서 Marker 속성이 있는 객체를 찾음
    mergeFigures([figN figN+len(figlIndexist)]) % 속도별로 합치기
    legend
    grid on
    % setlegendBoxShape(2)
    formatterFigure4Paper('double','2x2')
end
%% update per Speed 
for figIndex=len(CSVList)+1:len(CSVList)+len(CSVList)/2
    markerObjects = findobj(figure(figIndex), 'Type', 'Axes');
    markerObjects.ZLabel.String='P[kW]'
    markerObjects.XLabel.String='I_{d,pk}[A]'
    markerObjects.YLabel.String='I_{q,pk}[A]'
    legend
    lineobj=findobj(markerObjects,'Type','line')
    % setlegendBoxShape(len(lineobj))
    formatterFigure4Paper('double','2x2')
    grid on
end
% %% upated Per Model
% for figIndex=len(CSVList)+len(CSVList)/2+1:len(CSVList)+len(CSVList)/2+2
%     gcf=figure(figIndex)
%     markerObjects = findobj(gcf, 'Type', 'Axes');
%     markerObjects.ZLabel.String='P[kW]'
%     markerObjects.XLabel.String='I_{d,pk}[A]'
%     markerObjects.YLabel.String='I_{q,pk}[A]'
%     legend
%     lineobj=findobj(markerObjects,'Type','line')
%     setlegendBoxShape(len(lineobj))
%     formatterFigure4Paper('double','2x2')
%     grid on
% end

