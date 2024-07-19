function LabLinkTxtPath=makeLabLinkTXTFromLabTable(SatuMapTable,LabFileDir)

SatuMapTable=sortrows(SatuMapTable,'Is',"ascend");
% SatuMapTable.("Current Angle")=abs(SatuMapTable.("Current Angle"));
% SatuMapTable=sortrows(SatuMapTable,'Current Angle',"ascend");

%% 
if nargin==2
    if ~isfolder(LabFileDir)
    mkdir(LabFileDir)
    end
    % [b,~,~]=fileparts(b);
    LabLinkTxtPath=fullfile(LabFileDir,'LabLink.txt');
else    
    LabLinkTxtPath=fullfile(pwd,'LabLink.txt');
end

checkFileNMove(LabLinkTxtPath)

writetable(SatuMapTable,LabLinkTxtPath,'Delimiter','\t')

end