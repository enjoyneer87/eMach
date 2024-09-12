function mkJMAGResponseParameter(app,curStudyObj,DataSetName,StartValue,EndTime,PartName)
        parameter = app.CreateResponseDataParameter(DataSetName);
        parameter.SetCalculationType("SimpleAverage")
        parameter.SetStartValue(StartValue)
        parameter.SetEndValue(EndTime)
        parameter.SetUnit("s")
        if nargin<5
        parameter.SetAllLine(true)
        else
        parameter.SetAllLine(false)
        parameter.SetLine(PartName)
        end
        parameter.SetCaseRangeType(1)
        parameter.SetVariable(DataSetName)
        curStudyObj.UpdateParametricData(DataSetName, parameter)
end
