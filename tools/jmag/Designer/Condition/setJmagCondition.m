function JmagThermalConditionTable=setJmagCondition(JmagThermalConditionTable,ModelObj,studyObj)
    % setListTable=AssemTable.GeomSetList{AssemTableIndex}
    
    Steady2=studyObj;
    for ConditionIndex=1:height(JmagThermalConditionTable)

        %%[TB] Condition Type Properties Matrix Need to be mat File Data Base
        conditionTypeCell=cellstr(JmagThermalConditionTable.ConditionType(ConditionIndex));
        ConditionObj=Steady2.GetCondition(JmagThermalConditionTable.ConditionName{ConditionIndex});
        if ConditionObj.IsValid
        ConditionObj.GetName
        else
        ConditionObj            = Steady2.CreateCondition(conditionTypeCell{:}, JmagThermalConditionTable.ConditionName{ConditionIndex});
        end
        %% 해당 Condition  빈 속성 테이블 생성 
        conditionProperties     = ConditionObj.GetPropertyTable();
        ConditionPropertiesTable  = char2CategoricalPropertiesTable(conditionProperties);
        JmagThermalConditionTable.ConditionValueTable{ConditionIndex}=ConditionPropertiesTable;
        
        %% Set Face
        ConditionObj.AddSet(ModelObj.GetSetList().GetSet(JmagThermalConditionTable.GeomSetName{ConditionIndex}), 0)
        % ModelObj.GetSetList().GetSet(JmagThermalConditionTable.GeomSetName{ConditionIndex}).SetUpdateByRelation(true)
        %%[TB] Set Circuit IF have
        PropertiesNameList=cellstr(JmagThermalConditionTable.ConditionValueTable{ConditionIndex}.PropertiesName);
        if any(contains(PropertiesNameList,'Link'))
        CircuitComponentName =JmagThermalConditionTable.CircuitComponent{ConditionIndex};
        ConditionObj.SetLink(CircuitComponentName);
        end
        % %% Numof Copies If Have
        if any(contains(PropertiesNameList,'NumCopies'))
        % JmagThermalConditionTable.ConditionValueTable{ConditionIndex,1}.PropertiesValue{1} ;
        setJmagConditionPropertiesValue(JmagThermalConditionTable.ConditionValueTable{ConditionIndex},ConditionObj)
        end
    end
end