function DoeTable = addStructData2DoeTable(DoeStrcut, DoeTable)
    fieldDesignNumber=fieldnames(DoeStrcut)
    
    for fieldIndex=1:length(fieldDesignNumber)
        fieldName=fieldDesignNumber{fieldIndex}
        DesignIndex=find(strcmp((DoeTable.Properties.RowNames)',fieldName))
        if ~isempty(DesignIndex) && isfield(DoeStrcut.(fieldName),'SumofTotalLoss') && ~isempty(DoeStrcut.(fieldName).SumofTotalLoss.SumofTotalLoss)
            DoeTable(DesignIndex,:).SumofTotalLoss=DoeStrcut.(fieldName).SumofTotalLoss.SumofTotalLoss;
        end
    end
end