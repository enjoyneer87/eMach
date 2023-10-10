function ACLossTable = convertACLossArray2Table(ModelBuildPoints_Gamma_Lab, ModelBuildPoints_Current_Lab, OriginAC, conductorNumbers)
    ACLossTable=table();
    for i=1:ModelBuildPoints_Gamma_Lab*ModelBuildPoints_Current_Lab
        ACLossTable.(['casePerpkBeta',num2str(i)])=OriginAC((conductorNumbers-1)*(i-1)+2:(1+(conductorNumbers-1)*i),1);
    end
    ACLossTable.Properties.RowNames = generateStrCellArray('AC Copper Loss (C', 2, conductorNumbers, ')');
    % 첫행
    initialLineTable =array2table([OriginAC(1,1),zeros(1,width(ACLossTable)-1)]);
    initialLineTable.Properties.VariableNames=ACLossTable.Properties.VariableNames;
    initialLineTable.Properties.RowNames=generateStrCellArray('AC Copper Loss (C', 1, 1, ')');
    % 합치기
    ACLossTable=[initialLineTable;ACLossTable];
    transposedTable =rows2vars(ACLossTable,'VariableNamingRule','preserve');
    transposedTable.Properties.RowNames = transposedTable.OriginalVariableNames; % RowNames를 설정
    transposedTable=removevars(transposedTable,'OriginalVariableNames');
    ACLossTable=transposedTable;
    clear("transposedTable");
end