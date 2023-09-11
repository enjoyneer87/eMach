function LabLinkTxtPath=devSatuaMapTable2TXTinLabLinkFormat(ScaledSatuMapTable)
% replaceUnderscoresWithSpace
% defMCADLabLinkFortCell
%
newTable               =replaceUnderscoresWithSpace(ScaledSatuMapTable);
newTable               = sortrows(newTable,19,"ascend");
WIndex                 =find(contains(newTable.Properties.VariableUnits,'W')&~strcmp('W',newTable.Properties.VariableUnits));
LossCoefficientCell    =newTable.Properties.VariableNames(WIndex)';
LabLinkCell            =changeIronLossCell2LabLinkFormat(LossCoefficientCell);
NewTable               =replaceTableNamebyCell(newTable,LossCoefficientCell,LabLinkCell);
NewTable               =replaceMCADSatuMapTableName2LabLinkName(NewTable);

LabLinkFormatNameCell  =defMCADLabLinkFortCell(TeslaSPlaidGeometry);
table4txt               =filterAndSortVarTablebyNameCell(NewTable,LabLinkFormatNameCell);

LabLinkTxtPath=fullfile(pwd,'LabLink.txt');
writetable(table4txt,LabLinkTxtPath,'Delimiter','\t')
end 