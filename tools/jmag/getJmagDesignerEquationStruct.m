function equationStruct=getJmagDesignerEquationStruct(app)
    Model=app.GetCurrentModel;
    Study=app.GetCurrentStudy;
    CurrentDesignTable=Study.GetDesignTable();
    NumParameters=CurrentDesignTable.NumParameters;

    for parameterIndex=1:NumParameters
        if CurrentDesignTable.IsValid
        equationStruct(parameterIndex).object=CurrentDesignTable.GetEquation(parameterIndex-1);
            if  equationStruct(parameterIndex).object.IsValid
                equationStruct(parameterIndex).Name              = equationStruct(parameterIndex).object.GetName;
                equationStruct(parameterIndex).Expression        = equationStruct(parameterIndex).object.GetExpression;
                equationStruct(parameterIndex).DisplayName       = equationStruct(parameterIndex).object.GetDisplayName;
                equationStruct(parameterIndex).Type              = equationStruct(parameterIndex).object.GetType;
                equationStruct(parameterIndex).Description       = equationStruct(parameterIndex).object.GetDescription;
                equationStruct(parameterIndex).Modeling          = equationStruct(parameterIndex).object.GetModeling;
                equationStruct(parameterIndex).TrueValue          = equationStruct(parameterIndex).object.GetTrueValue;
            end

        end
    end

end