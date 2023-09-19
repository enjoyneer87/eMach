function LabLinkTxtPath=devSatuaMapTable2TXTinLabLinkFormat(ScaledSatuMapTable,MachineData,varargin)
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

LabLinkFormatNameCell  =defMCADLabLinkFortCell(MachineData);
table4txt               =filterAndSortVarTablebyNameCell(NewTable,LabLinkFormatNameCell);
table4txt=sortrows(table4txt,'Is',"ascend");

table4txt.("Current Angle")=abs(table4txt.("Current Angle"));
table4txt=sortrows(table4txt,'Current Angle',"ascend");

if nargin==3
    LabMatFileDir=varargin{1};
    [~,b,~]=fileparts(fileparts(fileparts(LabMatFileDir)));
    LabLinkTxtPath=fullfile(LabMatFileDir,[b,'LabLink.txt']);
else    
    LabLinkTxtPath=fullfile(pwd,'LabLink.txt');
end

writetable(table4txt,LabLinkTxtPath,'Delimiter','\t')

end 