function LabLinkTxtPath=devSatuaMapTable2TXTinLabLinkFormat(SatuMapTable,MachineData,varargin)
%% devSatuaMapTable2TXTinLabLinkFormat -> convertSatuMapTable2TXTinLabLinkFormat
% Used Function
    % replaceUnderscoresWithSpace
    % changeIronLossCell2LabLinkFormat
    % defMCADLabLinkFortCell -> defMCADLabLinkFormatCell
    % replaceTableNamebyCell
    % replaceMCADSatuMapTableName2LabLinkName
    % filterAndSortVarTablebyNameCell

% SatuMapTable can be SatumapTable or ScaledSatuMapTable

newTable               =replaceUnderscoresWithSpace(SatuMapTable);
newTable               = sortrows(newTable,'Phase Advance',"ascend");
%% Iron Loss 이름 
WIndex                 =find(contains(newTable.Properties.VariableUnits,'W')&~strcmp('W',newTable.Properties.VariableUnits));
LossCoefficientCell    =newTable.Properties.VariableNames(WIndex)';
LabLinkCell            =changeIronLossCell2LabLinkFormat(LossCoefficientCell);
%이름 바꾸기
changedOriginalTable               =replaceTableNamebyCell(newTable,LossCoefficientCell,LabLinkCell);
changedOriginalTable               =replaceMCADSatuMapTableName2LabLinkName(changedOriginalTable);

%%
LabLinkFormatNameCell  =defMCADLabLinkFormatCell(MachineData);
% table 4 txt
table4txt               =filterAndMergeTables(changedOriginalTable,LabLinkFormatNameCell,MachineData);
%
table4txt=sortrows(table4txt,'Is',"ascend");
table4txt.("Current Angle")=abs(table4txt.("Current Angle"));
table4txt=sortrows(table4txt,'Current Angle',"ascend");

if nargin==3
    LabMatFileDir=varargin{1};
    if ~isfolder(LabMatFileDir)
    mkdir(LabMatFileDir)
    end
    [~,b,~]=fileparts(LabMatFileDir);
    LabLinkTxtPath=fullfile(LabMatFileDir,[b,'LabLink.txt']);
else    
    LabLinkTxtPath=fullfile(pwd,'LabLink.txt');
end

writetable(table4txt,LabLinkTxtPath,'Delimiter','\t')

end 