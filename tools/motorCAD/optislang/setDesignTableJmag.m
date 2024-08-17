
pyrun("from win32com import client ")
pyrun("app = client.dynamic.Dispatch('designer.Application.210')")

currentModel=app.GetCurrentModel()
casearray = [0 for i in range(1)]
casearray[0] = 1

app.GetModel(u"s4v4_r9").DuplicateStudyWithCases(u"Lambda", u"NewLambda", casearray, u"", False)
currentModel.DeleteStudy('Lambda')
currentStudy=currentModel.GetStudy('NewLambda')


DesignTable=currentStudy.GetDesignTable()
DesignTable.AddParameterVariableName("CS1 (3PhaseCurrentSource): Amplitude",'Current')
DesignTable.AddParameterVariableName("CS1 (3PhaseCurrentSource): PhaseU",'phaseAdvance')
DesignTable.AddParameterVariableName(u'Study Properties: Step')


app.GetModel(u's4v4_r9').GetStudy(u'Lambda').GetDesignTable()
