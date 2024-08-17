function StepData = defSinglePeriodFromStudyTable(JMAGStudyTable)

% StepObj=SinStudyObj.GetStep;
% EndTime=StepObj.GetValue('EndPoint')
% StepDivision=StepObj.GetValue('StepDivision')

StepTable=JMAGStudyTable.StepTable{:};
% 
% %%
% matchingRows2Table = filterMCADTableWithAnyInfo(MCADTable, 'StepDivision','propertiesName')
StepDivisionValue=getTableValuebyName(StepTable,'StepDivision');
StepDivision=StepDivisionValue{:};
EndPointTable = filterMCADTableWithAnyInfo(StepTable, 'EndPoint','PropertiesName');
EndTime= EndPointTable.("PropertiesValue"){:};

StepData.EndTime=EndTime;
StepData.StepDivision=StepDivision;

end