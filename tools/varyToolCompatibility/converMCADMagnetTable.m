% DataImport
function TotalData=converMCADMagnetTable(N42EH)


%% Type=1 BH Curve
BValueTable = filterMCADTableWithAnyInfo(N42EH, 'BValue','AutomationName');
if isempty(BValueTable)
%% Type=2 Direct Input
MagnetTable = filterMCADTableWithAnyInfo(N42EH, 'Magnet','AutomationName');
MagnetTable.Value=str2double(MagnetTable.Value);
TotalData.MagnetTable=MagnetTable;
else
    HValueTable = filterMCADTableWithAnyInfo(N42EH, 'HValue','AutomationName');
kHValueTable = filterMCADTableWithAnyInfo(HValueTable, 'KhValue','AutomationName',1);
TempTable = filterMCADTableWithAnyInfo(N42EH, 'Temperature','AutomationName');
TempTable = filterMCADTableWithAnyInfo(TempTable, 'Valid','AutomationName',1);


NonBvalue = filterMCADTableWithAnyInfo(N42EH, 'BValue','AutomationName',1);
NonBHvalue = filterMCADTableWithAnyInfo(NonBvalue, 'HValue','AutomationName',1);
NonBHTempvalue = filterMCADTableWithAnyInfo(NonBHvalue, 'Temperature','AutomationName',1);


Bvalue=BValueTable.Value;
Hvalue=HValueTable.Value;
TempValue=TempTable.Value;
TotalTable=table(TempValue,Bvalue,Hvalue);
TotalTable.Properties.VariableUnits=["degC","Tesla","Amps/m"];
str4DataCellPerTemp  = struct();
str4DataTablePerTemp = struct();
    for i = 1:numel(TemperatureData)
        % 현재 온도에 해당하는 행 선택
        currentTemp = TemperatureData(i);
        tempTable = TotalTable(TotalTable.TempValue == currentTemp, :);    
        % 구조체에 저장
        if currentTemp<0
        fieldName = ['DataAtTempMinus', num2str(abs(currentTemp))];
        else
        fieldName = ['DataAtTemp', num2str(currentTemp)];
        end
        str4DataCellPerTemp.(fieldName) = num2cell([tempTable.Hvalue,tempTable.Bvalue]);
        str4DataTablePerTemp.(fieldName) = table(tempTable.Hvalue,tempTable.Bvalue);
        str4DataTablePerTemp.(fieldName).Properties.VariableNames={'Hvalue','Bvalue'};
        str4DataTablePerTemp.(fieldName).Properties.Description=['Temp=',num2str(currentTemp)];
    end
    
    TotalData.str4DataCellPerTemp   =str4DataCellPerTemp;
    TotalData.str4DataTablePerTemp  =str4DataTablePerTemp;
    TotalData.NonBHTempTable=NonBHTempvalue;
    TotalData.TotalTable=TotalTable;
end

end