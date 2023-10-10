function ActiveXStr=loadMCadActiveXParameter()
    addpath(genpath(pwd))
    ActiveXStr=load('mcadActiveXparameterList.mat');
    % fieldNames=fieldnames(x.ActiveXParametersStruct);
    % for fieldIndex=1:length(fieldNames)
    %     fieldName=fieldNames{fieldIndex};
    % x.ActiveXParametersStruct.(fieldName).Properties.RowNames=cellstr(num2str(x.ActiveXParametersStruct.(fieldName).Number));
    % end
    % ActiveXParametersStruct=MCadActiveXParameter.a
    % save('mcadActiveXparameterList.mat','ActiveXParametersStruct')
end