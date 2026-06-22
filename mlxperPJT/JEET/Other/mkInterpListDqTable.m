% FqTable
% for LossIndex=1:1
%     for csvindex=1:height(FqTable)
%     interpList{csvindex,LossIndex}.FqTable=FqTable.dqTable{csvindex}(:,[1:2,LossIndex+2]);
%     % interpList{csvindex,LossIndex}.SCLTable=SCLTable.dqTable{csvindex}(:,[1:2,LossIndex+2]);
%     InputTable=FqTable.dqTable{csvindex}(:,[1:2,LossIndex+2]);
%     PlotName=InputTable.Properties.VariableNames{3};
%     [tempFitResult, tempGof, tempSingleDataSet] = createInterpDataSetofStrWithFieldName(InputTable, PlotName);
%     end
% end
% 
% figure(8)
% % ax=plot(tempFitResult)



%%


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