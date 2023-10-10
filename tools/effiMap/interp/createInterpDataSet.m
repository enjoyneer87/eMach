function [fitresult, gof, DataSet] = createInterpDataSet(Data4Interp, varName)

if istable(Data4Interp)
    InputTable=Data4Interp;
elseif isstruct(Data4Interp)
    [InputTable,~] = createTableFromMCADSatuMapStr(Data4Interp);
else 
    error('올바른 데이터를 입력하세요');
end
    
varNames=InputTable.Properties.VariableNames;
varUnits=InputTable.Properties.VariableUnits;

nonAmpereIndex=~strcmp(varUnits,'A');
varNamesNonAmperes=varNames(nonAmpereIndex);

    if nargin==2
        [fitresult, gof, DataSet] = createInterpDataSetofStrWithFieldName(InputTable, varName);
    else
        for varIndex=1:length(varNamesNonAmperes)
        varName=varNamesNonAmperes{varIndex};    
        [fitresult{varIndex}, gof(varIndex), DataSet(varIndex)] = createInterpDataSetofStrWithFieldName(InputTable, varName);
        end
    end

end
   
