function [cleanedMatrix,normalizedTable]=normlizeDOETable(Sensitivity1)
normalizedData = table2array(Sensitivity1);
normalizedData(:,1:end) = (normalizedData(:,1:end) - mean(normalizedData(:,1:end))) ./ std(normalizedData(:,1:end));
cleanedMatrix = removeColumnsWithNaN(normalizedData);
normalizedTable = array2table(cleanedMatrix, 'VariableNames', Sensitivity1.Properties.VariableNames);
end