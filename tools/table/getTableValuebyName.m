function valueFind=getTableValuebyName(table2target,name2find)
% table2target=equationTable
% name2find='Ro_yoke'

%% Properties VariableNames
VariableNames=table2target.Properties.VariableNames;
nameIndexinTable=find(contains(VariableNames,'name','IgnoreCase',true));
valueIndexinTable=find(contains(VariableNames,'value','IgnoreCase',true));
%% 
valueIndex=find(contains(table2target.(VariableNames{nameIndexinTable}),name2find));

%% Value2 find
valueFind=table2target.(VariableNames{valueIndexinTable})(valueIndex);
end