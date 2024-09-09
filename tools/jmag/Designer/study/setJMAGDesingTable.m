function settedDTTable=setJMAGDesingTable(curStudyObj,ParameterListTable)
    DTTable          =curStudyObj.GetDesignTable;
    NumCase          =DTTable.NumCases;
    NumParameters=DTTable.NumParameters;
for caseIndex=1:NumCase
    for ParIndex=1:NumParameters
         if iscell(ParameterListTable{caseIndex,ParIndex})
             value2Input=ParameterListTable{caseIndex,ParIndex}{1};
         else
             value2Input=ParameterListTable{caseIndex,ParIndex};
         end
         DTTable.SetValue(caseIndex-1, ParIndex-1,value2Input);
    end
end

    settedDTTable=getJMAGDesingTable(curStudyObj);

end