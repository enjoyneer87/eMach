%% rp 
%% MS HYB
%% TS 
%% FQ 

%% FQ - REF 64k-16k-4k ratio
%% REF TS/FQ 64k/64k 16k/16 - 4k/4k 
% 16k/16k

speedIdx=4    
figure(speedIdx)
InputTable=REFTable.dqTable{speedIdx}(:,[1:2,LossIndex]);
InputTable.Is=InputTable.Is*2
PlotName=InputTable.Properties.VariableNames{3};  
[tempFitResult, tempGof, tempSingleDataSet] = createInterpDataSetofStrWithFieldName(InputTable, PlotName);
[surfTSREF(speedIdx)]=plotSurf2ndPlane(tempSingleDataSet.xData,tempFitResult);


hold on
speedIdx=1
InputTable=SCLTable.dqTable{speedIdx}(:,[1:2,LossIndex]);
PlotName=InputTable.Properties.VariableNames{3};  
[tempFitResult, tempGof, tempSingleDataSet] = createInterpDataSetofStrWithFieldName(InputTable, PlotName);
[surfTSSCL(speedIdx)]=plotSurf2ndPlane(tempSingleDataSet.xData,tempFitResult);
    surfTSSCL(speedIdx).FaceAlpha=0.2; 
    surfTSSCL(speedIdx).LineStyle="--"

 %% def
   


  simulRPM= TargetTable.speedK(speedIdx)*1000;f


for speedIdx=1:height(REFTable)-1    
figure(speedIdx)
InputTable=SCLFqTable.dqTable{speedIdx}(:,[1:2,LossIndex]);
% InputTable.Is=InputTable.Is*2
PlotName=InputTable.Properties.VariableNames{3};  
[tempFitResult, tempGof, tempSingleDataSet] = createInterpDataSetofStrWithFieldName(InputTable, PlotName);
[surfTSREF(speedIdx)]=plotSurf2ndPlane(tempSingleDataSet.xData,tempFitResult);


hold on
InputTable=SCLTable.dqTable{speedIdx}(:,[1:2,LossIndex+2]);
PlotName=InputTable.Properties.VariableNames{3};  
[tempFitResult, tempGof, tempSingleDataSet] = createInterpDataSetofStrWithFieldName(InputTable, PlotName);
[surfTSSCL(speedIdx)]=plotSurf2ndPlane(tempSingleDataSet.xData,tempFitResult);
    surfTSSCL(speedIdx).FaceAlpha=0.2; 
    surfTSSCL(speedIdx).LineStyle="--"
end
