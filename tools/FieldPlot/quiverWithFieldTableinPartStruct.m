function quiverWithFieldTableinPartStruct(WireStruct,PartIndex,~)
    if nargin==3
        PlotType='Transient'
    else
        PlotType='Static'
        NumSteps=1;
    end

% WireStruct(1).BxTimeinRow.Properties.VariableNames
    
    VarNames=WireStruct(PartIndex).ElementPosition.Properties.VariableNames;

    for ElementIndex=1:length(VarNames)
        ElementIDStr=VarNames{ElementIndex};
        ElementPostion=WireStruct(PartIndex).ElementPosition.(ElementIDStr);
           
        containCell=findMatchedVarName(WireStruct(1).BxTimeinRow,ElementIDStr,1);
        BxFieldData=WireStruct(1).BxTimeinRow.(containCell{:});
        ByFieldData=WireStruct(1).ByTimeinRow.(containCell{:});
    
        % ElementID=strrep(,'x',"");
        if strcmp(PlotType,'Transient')
            NumSteps=length(BxFieldData)
        end
        for rowIndex=1:NumSteps
         quiver(ElementPostion(1),ElementPostion(2),BxFieldData(rowIndex,1),ByFieldData(rowIndex,1),'r')
         hold on
        end
    
    end


end