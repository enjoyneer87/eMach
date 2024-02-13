function LabLinkTxtPath=makeLabLinkTXTFromLabTable(SatuMapTable,LabMatFileDir)

SatuMapTable=sortrows(SatuMapTable,'Is',"ascend");
% SatuMapTable.("Current Angle")=abs(SatuMapTable.("Current Angle"));
% SatuMapTable=sortrows(SatuMapTable,'Current Angle',"ascend");

%%
if nargin==2
    if ~isfolder(LabMatFileDir)
    mkdir(LabMatFileDir)
    end
    [~,b,~]=fileparts(LabMatFileDir);
    LabLinkTxtPath=fullfile(LabMatFileDir,[b,'LabLink.txt']);
else    
    LabLinkTxtPath=fullfile(pwd,'LabLink.txt');
end

checkFileNMove(LabLinkTxtPath)

writetable(SatuMapTable,LabLinkTxtPath,'Delimiter','\t')

end