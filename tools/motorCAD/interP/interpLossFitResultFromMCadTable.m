function [fitResult, LossDataInfo] = interpLossFitResultFromMCadTable(MCADTable, varNameList)
    fitResult = struct();
    LossDataInfo = struct();
    lossTypes = {'Hys', 'Eddy', 'AC Copper', 'Magnet'};
    
    for i = 1:length(lossTypes)
        varIndexList = find(contains(varNameList, lossTypes{i}));
        for j = 1:length(varIndexList)
            varName = varNameList{varIndexList(j)};
            [fit, gof, DataSet] = createInterpDataSet(MCADTable, varName);
            fieldName=replaceSpacesWithUnderscores(lossTypes{i});
            fitResult.(fieldName)(j) = struct('Name', varName, 'fitResult', fit, 'gof', gof);
            LossDataInfo.(fieldName)(j).xData = DataSet.xData;
            LossDataInfo.(fieldName)(j).yData = DataSet.yData;
            LossDataInfo.(fieldName)(j).zData = DataSet.zData;
            LossDataInfo.(fieldName)(j).varName=DataSet.varName;
            LossDataInfo.(fieldName)(j).originDqTable.Properties.Description=MCADTable.Properties.Description;
            

        end
    end

end