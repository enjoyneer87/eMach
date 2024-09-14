JMAGParentPath='D:\KangDH\Thesis\e10';
parentPath='F:\KDH\Thesis\JEET'
[motFileList,~]=getResultMotMatList(parentPath)

% Plot AC Loss Map
% try Final function
filteredTable           =getMCADLabDataFromMotFile(motFileList{1});
originLabLinkTable      = reNameLabTable2LabLink(filteredTable);
MCADLinkTable           = originLabLinkTable;
plotMultipleInterpSatuMapSubplots(@plotFitResult, MCADLinkTable);
close all


ACLossVarList=MCADLinkTable.Properties.VariableNames
BooACLossVar=contains(ACLossVarList,'AC')
ACLossVarIndex=find(BooACLossVar)
for LossIndex=1:4
    InputTable=MCADLinkTable(:,[1:2 ACLossVarIndex(LossIndex)]);
    PlotName=ACLossVarList{ACLossVarIndex(LossIndex)};
    [tempFitResult, tempGof, tempSingleDataSet] = createInterpDataSetofStrWithFieldName(InputTable, PlotName);
    interpList{LossIndex}.REFFIt     =tempFitResult;
    interpList{LossIndex}.DataSet=tempSingleDataSet;
    plot(interpList{LossIndex}.REFFIt)
    hold on
end

    InputTable=MCADLinkTable(:,[1:2]);

addvars(InputTable,MCADLinkTable(:,[ACLossVarIndex(LossIndex)]).Variables)
for LossIndex=1:4
    InputTable=addvars(InputTable,MCADLinkTable(:,[ACLossVarIndex(LossIndex)]).Variables)    
end


TotalACLossTable=MCADLinkTable(:,[1:2])
TotalACLossTable=addvars(TotalACLossTable,TotalACLoss./1000.*(18000/500).^2.+0.3*(18000/9000).^2,'NewVariableNames','TotalACLoss')

3954/1000+
[MCADFitResult, tempGof, tempSingleDataSet] = createInterpDataSetofStrWithFieldName(TotalACLossTable,'TotalACLoss');
plot(MCADFitResult)
hold on
plot(interpList{4,3}.REFFIt)
18000/1800^2
log10(0.04297/0.0007207)

