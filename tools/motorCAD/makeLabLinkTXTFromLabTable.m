function LabLinkTxtPath=makeLabLinkTXTFromLabTable(SatuMapTable,LabMatFileDir)

SatuMapTable=sortrows(SatuMapTable,'Is',"ascend");
% SatuMapTable.("Current Angle")=abs(SatuMapTable.("Current Angle"));
% SatuMapTable=sortrows(SatuMapTable,'Current Angle',"ascend");


%% AC Loss C1추가 (Plot할때 2배하는거는 PlotFit에서 처리)
SatuMapTable.("AC Copper Loss (C1)")=zeros(height(SatuMapTable),1);
SatuMapTable=movevars(SatuMapTable,"AC Copper Loss (C1)","Before","AC Copper Loss (C2)");

% for i=1:length(ACLossCell)
%     AClossString=ACLossCell{i};
%     ACLossCellStartIndex = strfind(AClossString, 'Loss_(C');
%     ACLossCellEndIndex = strfind(AClossString, ')');
%     cuboidNumber=AClossString(ACLossCellStartIndex+length('Loss_(C'):ACLossCellEndIndex-1);
%     newCoboidNumber=str2num(cuboidNumber)-1;   
%     inputTable.Properties.VariableNames=strrep(inputTable.Properties.VariableNames,['(C',cuboidNumber,')'],['(C',num2str(newCoboidNumber),')']);
%     ACLossCell=strrep(ACLossCell,['(C',cuboidNumber,')'],['(C',num2str(newCoboidNumber),')']);
% end

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

writetable(SatuMapTable,LabLinkTxtPath,'Delimiter','\t')

end