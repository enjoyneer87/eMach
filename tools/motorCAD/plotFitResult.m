function plotFitResult(fitresult, DataSet,plotDatatype)
%%
    if ~isempty(DataSet) && strcmp(class(fitresult),'sfit')
        if isfield(DataSet,'ValidationDqTable')
         plotFitResultwithValidation(fitresult,DataSet,plotDatatype)
        else     
         plotFitResultWithoutValidation(fitresult,DataSet,plotDatatype)
        end
    end
end