function ParameterListTable=getJMAGDesingTable(curStudyObj)
DTTable          =curStudyObj.GetDesignTable;
NumCase          =DTTable.NumCases;
AllParameterNames=DTTable.AllParameterNames;
NumParameters=DTTable.NumParameters;

ParameterNameLists=cell(NumParameters,1);
ParameterLists    =cell(NumCase,NumParameters);
for caseIndex=1:NumCase
    for ParIndex=1:NumParameters
        ParameterNameLists{ParIndex,1}=DTTable.ParameterName(ParIndex-1);
        realPartIndex=DTTable.GetParameterIndex(ParameterNameLists{ParIndex,1});
        % ParameterTypeName{ParIndex,1}=DTTable.ParameterTypeName(realPartIndex);
        ParameterLists{caseIndex,realPartIndex+1}=DTTable.GetValue(caseIndex-1,realPartIndex);
    end
end

ParameterListTable=cell2table(ParameterLists);
ParameterListTable.Properties.VariableNames=ParameterNameLists;

end