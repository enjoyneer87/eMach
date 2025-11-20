function [cleanedMatrix,normalizedTable,Sensitivity1]=normlizeDOETable(Sensitivity1)
    LowUniqueVariables = findLowUniqueVariables(Sensitivity1, 5);
    Sensitivity1 = removevars(Sensitivity1,LowUniqueVariables);
    Sensitivity1 = removeUniformValueVariables(Sensitivity1,1e-6);

    normalizedData = table2array(Sensitivity1);
    normalizedData(:,1:end) = (normalizedData(:,1:end) - mean(normalizedData(:,1:end))) ./ std(normalizedData(:,1:end));
    [cleanedMatrix,nanColumns] = removeColumnsWithNaN(normalizedData);
    normalizedTable = array2table(cleanedMatrix, 'VariableNames', Sensitivity1.Properties.VariableNames(~nanColumns));
end