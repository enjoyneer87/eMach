function [fitresult, gof, DataSet] = plotInterpSurfNResidualTableWithVar(originDqTable, ValidationDqTable, varName)   
    [fitresult, gof, DataSet] = interpSurfNResidualTwoTableWithVar(originDqTable, ValidationDqTable, varName);
    plotFitResultwithValidation(fitresult, DataSet);
end