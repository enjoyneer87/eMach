clear krk
scFactor=[1 2]
for SCIndex=1:2
    coeffixi=calckXi4EddyLoss(mm2m(1.6*scFactor(SCIndex)),mm2m(3.7*scFactor(SCIndex)),mm2m(5*scFactor(SCIndex)),600)
    psiXi=calcProxyEffFun(coeffixi)
    for k=1:4
    krk{scFactor(SCIndex),k}=k*(k-1)*psiXi;
    end
    plot([krk{scFactor(SCIndex),:}])
    hold on
end

krk{2,4}/krk{2,2}
krk{scFactor(SCIndex),4}/krk{scFactor(SCIndex),2}
krk{1,4}/krk{1,2}
krk{scFactor(SCIndex),2}/krk{1,2}
%% 
app=callJmag
ecsv=exportJMAGAllCaseTables(app,'JEET')
tempCSVPath='D:\KangDH\Emlab_emach\mlxperPJT\JEET\From38100\SCL_e10_WTPM_PatternD_R1_9kMap_SC_e10_WirePeriodic_Load_9k_rough240steps.csv'
ResultCSVPath{PJTStudyIndex}=tempCSVPath
ResultTableFromCSVPerStudy     =readtable(tempCSVPath,opts);
a=fullfile(ResultCSVDir,['ResultTabStudy',StudyName,'.mat'])
MatFileName='MQS TS FEA';

filterName='9k'
[parsedMSResultTableFromCSV,ResultCSVPath]=readJMAGWholeResultTables('SCL');

% [parsedMSResultTableFromCSV,ResultCSVPath]=readJMAGWholeResultTables(FqfilterName);
% AppNumStudies=len(parsedMSResultTableFromCSV);
% save([defaultJEETPath,MatFileName,'.mat'],"parsedMSResultTableFromCSV")

MatFileList=findMatFiles(pwd);
MatFileList=MatFileList(contains(MatFileList,'ResultTab',"IgnoreCase",true));
MatFileList=MatFileList(~contains(MatFileList,'Fq',"IgnoreCase",true));
AppNumStudies=len(MatFileList);
PatternList={'PatternC','PatternD'};
MatFileList={'D:\KangDH\Emlab_emach\mlxperPJT\JEET\From38100\ResultTabStudySCL_e10_WTPM_PatternD_R1_9kMap_SC_e10_WirePeriodic_Load_9k_rough240steps.mat'}
speedList=[1000:2000:14000];
AppStudyIndex=1
for AppStudyIndex=1:AppNumStudies
    load(MatFileList{AppStudyIndex})
    if contains(MatFileList{AppStudyIndex},'SCL')
    figure(2)
    DispName='SLC'
    else
    figure(1)
    DispName='REF';
    end
    %%
    tempJouleLossTableCell=parsedResultTable5StudyPerStudy.("JouleLoss:W");
    speedList=zeros(1,len(tempJouleLossTableCell));
    JouleAvgTablCell4Case=cell(len(speedList),2);
    speedNameList=cell(1,len(tempJouleLossTableCell));
    for caseIndex=1:height(tempJouleLossTableCell)
        table2Plot=tempJouleLossTableCell{caseIndex};
        
        BoolwireProp=contains(table2Plot.Properties.VariableNames,'Wire','IgnoreCase',true)
        TotalAC=mean(table2Plot(end-240:end,'Total').Variables)/1000
        WireTable=table2Plot(:,BoolwireProp)
        BoolWire4=contains(WireTable.Properties.VariableNames,'Wire4','IgnoreCase',true)
        W4Table=WireTable(end-240:end,BoolWire4)
        BoolWire2=contains(WireTable.Properties.VariableNames,'Wire2','IgnoreCase',true)
        W2Table=WireTable(end-240:end,BoolWire2)
        BoolWire1=contains(WireTable.Properties.VariableNames,'Wire1','IgnoreCase',true)
        W1Table=WireTable(end-240:end,BoolWire1)
        BoolWire3=contains(WireTable.Properties.VariableNames,'Wire3','IgnoreCase',true)
        W3Table=WireTable(end-240:end,BoolWire3)
        plot(W4Table.Time,W4Table(:,:).Variables)

    

        figure(1)
        plot(W1Table,"Time","Stator_Slot1_Wire1",'Color','g','Marker','o')
        
        hold on
        plot(W1Table,"Time","Stator_Slot7_Wire1",'LineStyle','--','LineWidth',2,'Color','k','Marker','x')
        plot(W3Table,"Time","Stator_Slot7_Wire3",'LineStyle','--','LineWidth',2,'Color','k','Marker','x')

        % layer 3
        plot(W3Table,"Time","Stator_Slot1_Wire3",'Color','g','Marker','o')
        hold on
        %% Slot 78
        plot(W2Table,"Time","Stator_Slot7_Wire2",'LineWidth',2,"Color",'g','Marker','x')
        hold on
        hold on
        plot(W4Table,"Time","Stator_Slot7_Wire4",'LineWidth',2,"Color",'g','Marker','x')
        hold on
        legend

        figure(2)
        hold on

        plot(W1Table,"Time","Stator_Slot2_Wire1",'LineStyle','--','Color',0.8*[0 255 0]/256,'Marker','o')
        plot(W3Table,"Time","Stator_Slot2_Wire3",'LineStyle','--','Color',0.8*[0 255 0]/256,'Marker','o')
        plot(W2Table,"Time","Stator_Slot8_Wire2",'LineStyle','--','LineWidth',2,"Color",0.8*[0 255 0]/256,'Marker','x')
        plot(W4Table,"Time","Stator_Slot8_Wire4",'LineStyle','--','LineWidth',2,'Color',0.8*[0 255 0]/256,'Marker','x')       

        %% 
        cont1=W1Table.Stator_Slot1_Wire1+W2Table.Stator_Slot7_Wire2
        cont2=W1Table.Stator_Slot2_Wire1+W2Table.Stator_Slot8_Wire2
        cont3=W3Table.Stator_Slot1_Wire3+W4Table.Stator_Slot7_Wire4
        cont4=W3Table.Stator_Slot2_Wire3+W4Table.Stator_Slot8_Wire4
        sum(mean([cont1 cont2 cont3 cont4]))/1000*6
        plot([cont1 cont2 cont3 cont4])
        %% 
        
         mean(W4Table.Stator_Slot1_Wire4./W2able.Stator_Slot1_Wire2)
        wire42=mean(W4Table.Stator_Slot1_Wire4)+mean(W4Table.Stator_Slot2_Wire4)+mean(W2Table.Stator_Slot7_Wire2)+mean(W2Table.Stator_Slot8_Wire2)
        wire13=mean(W1Table.Stator_Slot1_Wire1)+mean(W1Table.Stator_Slot2_Wire1)+mean(W3Table.Stator_Slot7_Wire3)+mean(W3Table.Stator_Slot8_Wire3)
        TotalAC/((wire42+wire13)/1000*3*2)
        % tempJouleLossTable{caseIndex}        =table2Plot.Total;
        % Name List
        speedList(caseIndex)=freqE2rpm(1/seconds(table2Plot.Time(121)),4);
        speedNameList{1,caseIndex}=['case',num2str(caseIndex),'speed',num2str(speedList(caseIndex))];
        %
        JouleAvgTablCell4Case{caseIndex,2}=mean(table2Plot(end-120:end,'Total').Variables);
        JouleAvgTablCell4Case{caseIndex,1}=table2Plot(end-120:end,'Total').Variables;
    end
    JouleAvgTablCell4CaseTable=cell2table(JouleAvgTablCell4Case);
    JouleAvgTablCell4CaseTable.Properties.VariableNames={'JouleTable','JouleAvg'};
    meanACLoss=[JouleAvgTablCell4Case{:,2}];
    if contains(MatFileList{AppStudyIndex},'PatternC')
        PatternIndex=1;
    else
        PatternIndex=2;
    end
    plot(speedList,meanACLoss/1000,'--','DisplayName',[MatFileName,PatternList{PatternIndex}]);
    title(DispName)
    hold on
    % JouleAvgTablCell4CaseTable.Properties.RowNames=speedList;
    % save([defaultJEETPath,MatFileName,num2str(AppStudyIndex),'.mat'],"JouleAvgTablCell4CaseTable")
end