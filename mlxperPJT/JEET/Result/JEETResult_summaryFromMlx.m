
SpeedList=[1000:1000:20000];
delta=calcSkinDepth(omega2freq(rpm2OmegaE(SpeedList,4))) % 2.25594 -
% delta>>h 가정에 대부분의 hairpin은 자유로울수 없음
d_limit=0.5*delta;
conductorDia=3
isinDlimit=conductorDia<d_limit
% Generate frequency range for the plot
% frequency = linspace(10, 2000); % Adjust range as needed
frequency = linspace(omega2freq(rpm2OmegaE(10,4)), omega2freq(rpm2OmegaE(20000,4))); % Adjust range as needed
% Calculate skin depth for each frequency
skin_depth = arrayfun(@calcSkinDepth, frequency);
% Plot the results
figure(4)
plot(frequency, skin_depth*0.5);
xlabel('Frequency (Hz)');
ylabel('Skin Depth (mm)');
title('Skin Depth vs Frequency');
grid on;
figure(5)
SpeedList=freq2rpm(elec2mech(frequency,4))
plot(SpeedList, skin_depth);
xlabel('Rotational Speed[RPM]');
ylabel('Skin Depth (mm)');
title('Skin Depth vs RPM');
grid on;

skinDepthList=[SpeedList,skin_depth]

%%
markerList={'+' , 'o' , '*' , '.' , 'x' , 'square' , 'diamond' , 'v' , '^' , '>' , '<' , 'pentagram' , 'hexagram' , ',' , '_' };

%% Juha

% close all
% 
Irms             =460;
[SCIdrms,SCIqrms]=pkgamma2dq(Irms*2,43.3)
ScaleList    =[1,2]
juhaspeedList=1000:2000:20000;
freqE=rpm2freqE(juhaspeedList,4)
REFdimensions=[3.7,1.6,5]
NtCoil=4


JuhaMatFileList=findMatFiles(pwd)
JuhaMatFileList=JuhaMatFileList(contains(JuhaMatFileList,'LossList'))'
LineList ={'--','-'}

for ScaleIndex=1:len(ScaleList)
    if ScaleIndex==2
    figure(1)
    linesty=LineList{2}
    DispName='SCL'
    else
    figure(1)
    linesty=LineList{1}
    DispName='REF'
    end
    dimension2Calc=REFdimensions*ScaleList(ScaleIndex)
    IrmsList             =Irms*ScaleList(ScaleIndex);
    DCLoss = 3 * 0.0068/(ScaleList(ScaleIndex).^2) * (IrmsList).^2
    [kr,varphiXi,ksi,psiXi]=calcHybridJouleLossJuHa(dimension2Calc,NtCoil,freqE)
    skinLoss=DCLoss*(varphiXi-1)/1000;
    proxLoss=DCLoss *(psiXi)*(4^2 - 0.2) / 3/1000;
    Pjoule = DCLoss*(varphiXi)/1000 +proxLoss;

    plot(juhaspeedList,skinLoss,linesty,'DisplayName','Skin Effect')
    hold on
    plot(juhaspeedList,Pjoule,linesty,'DisplayName','Joule Juha')
    plot(juhaspeedList,proxLoss,linesty,'DisplayName','Prox. Effect')

    title(DispName)
    legend
end


% plot(Pjoule)

%% MCAD


%% Matlab Jmag HYB -Prox

load('MSRMSesultTableFromCSV.mat')
MSRTargetTable      =MSRMSesultTableFromCSV.MSRTargetTable;
MSthetaTargetTable  =MSRMSesultTableFromCSV.MSthetaTargetTable;
refDim=[3.7 1.6 150]
pole=8
speedList=[1000:2000:20000];
refDim(3)=150;
SCDim=2*refDim
SCDim(3)=150

DimList={refDim,SCDim};
% Prox
speedList=[1000:2000:20000];
ModelList={'REF','SCL'}
for ModelNStudyIndex=1:2
    for speedIndex=1:len(speedList)
        speed=speedList(speedIndex);
        [JMAGHYB_px{ModelNStudyIndex}.TotalACLossPerMethod{speedIndex},DisplaynameList]=devcalcAllHybridACFromBtable(speed,pole,DimList{ModelNStudyIndex},MSRTargetTable{ModelNStudyIndex}{1,1},MSthetaTargetTable{ModelNStudyIndex}{1,1});
    end    
end
colorList={'k','b','r','y','g'};
MethodList={'Dowell','Rect1DG1','Rect2DG1','Rect1DG2','Rect2DG2'}
LineList ={'--','-'}
for ModelNStudyIndex=1:2
    for speedIndex=1:len(speedList)
         speed=speedList(speedIndex)
        % for MethodIndex=1:len(JMAGHYB_px{ModelNStudyIndex}.TotalACLossPerMethod{1})
        for MethodIndex=5:len(JMAGHYB_px{ModelNStudyIndex}.TotalACLossPerMethod{1})
            figure(10)
            curMethodWaveForm{speedIndex,MethodIndex}=JMAGHYB_px{ModelNStudyIndex}.TotalACLossPerMethod{speedIndex}{MethodIndex};
            % plot(curMethodWaveForm{speedIndex,MethodIndex}/1000,'color',colorList(speedIndex,:),'Marker',MarkerList{MethodIndex},'DisplayName',MethodList{MethodIndex})
            plot(curMethodWaveForm{speedIndex,MethodIndex}/1000*48,colorList{MethodIndex},'Marker',markerList{MethodIndex},'DisplayName',[ModelList{ModelNStudyIndex},'',MethodList{MethodIndex},' ',num2str(speed)])
            hold on
        end
    end
    for speedIndex=1:len(speedList)
        % for MethodIndex=1:len(JMAGHYB_px{ModelNStudyIndex}.TotalACLossPerMethod{1})
        for MethodIndex=5:len(JMAGHYB_px{ModelNStudyIndex}.TotalACLossPerMethod{1})
        avgHYBPxList(speedIndex,MethodIndex)=mean(curMethodWaveForm{speedIndex,MethodIndex}/1000*48+4.4)
        end
    end
    % for MethodIndex=1:len(JMAGHYB_px{ModelNStudyIndex}.TotalACLossPerMethod{1})
    for MethodIndex=5:len(JMAGHYB_px{ModelNStudyIndex}.TotalACLossPerMethod{1})
        figure(ModelNStudyIndex)
        plot(speedList(1:len(JMAGHYB_px{ModelNStudyIndex}.TotalACLossPerMethod)),avgHYBPxList(:,MethodIndex)',colorList{MethodIndex},'Marker',markerList{MethodIndex},'LineStyle',LineList{ModelNStudyIndex},'DisplayName',[MethodList{MethodIndex}])
        title(ModelList{ModelNStudyIndex})
        hold on
    end
end
%% SCL FQ

FqfilterName='fq'
MatFileListFq=findMatFiles(pwd);
MatFileListFq=MatFileListFq(contains(MatFileListFq,FqfilterName,"IgnoreCase",true));
FqfilterName='Pattern'
MatFileListFq=MatFileListFq(contains(MatFileListFq,FqfilterName,"IgnoreCase",true));

PatternList={'PatternC','PatternD'};
AppNumStudies=len(MatFileListFq)
% CurStudyObj=app.GetCurrentStudy
% addJMAGEqaution('sigma','',CurStudyObj)
% addJMAGEqaution('mu0',4*pi*10^-7 ,CurStudyObj)
% addJMAGEqaution('diffusionFactor',72.892 ,CurStudyObj)
% addJMAGEqaution('SkinDepth','sqrt(2/(omegaE*diffusionFactor))',CurStudyObj)
SkinDepth_delta_inmm = calcSkinDepth(rpm2freqE(8000,4))
% for AppStudyIndex=1:AppNumStudies
%     load(MatFileListFq{AppStudyIndex})
%     tempJouleLossTableCell=parsedResultTable5StudyPerStudy.("JouleLoss:W");
%     for caseIndex=1:height(tempJouleLossTableCell)
%         tempJouleLossTable{caseIndex}        =tempJouleLossTableCell{caseIndex}.Total;
%         freqEList=tempJouleLossTableCell{caseIndex}.Properties.RowNames;
%         RPMList=freq2rpm(elec2mech(convertCharCell2Numeric(freqEList),4))
%     end
%     for tableIndex=1:1
%         plot2Table=tempJouleLossTable{tableIndex};
%         if contains(MatFileListFq{AppStudyIndex},'SCL','IgnoreCase',true)
%         figure(2)
%         linesty=LineList{2}
%         DispName='SCL'
%         elseif contains(MatFileListFq{AppStudyIndex},'ref','IgnoreCase',true)
%         figure(1)
%         linesty=LineList{1}
%         DispName='REF'
%         end
%         plot(RPMList,plot2Table/1000,'DisplayName','FQ')
%         title(DispName)
%         hold on
%     end
% end

% 
% 
% ParameterListTable=getJMAGDesingTable(curStudyObj);
% Bool45degIndex=contains(ParameterListTable.("Equation parameters: MCADPhaseAdvance"),'45')
% FQspeedList=ParameterListTable.("Equation parameters: speed")(Bool45degIndex)
% Total45degJoule=TotalJoule(Bool45degIndex)
% FreqList=convertCharCell2Numeric(plot2Table.Properties.RowNames)
% RPMList=freq2rpm(elec2mech(FreqList,4))
% for tableIndex=1:len(Total45degJoule)
%     plot2Table=Total45degJoule{tableIndex}
%     DispName=['FQ SCL' FQspeedList{tableIndex}]
%     if contains(DispName,'SCL')
%     figure(2)
%     linesty=LineList{2}
%     else
%     figure(1)
%     linesty=LineList{1}
%     end
% 
%     plot(RPMList,plot2Table.('Total')/1000,'DisplayName',DispName)
%     hold on
% end
%% Total MQS

FqfilterName={'e10_WTPM_Pattern'};
MatFileName='MQS TS FEA';
% [parsedMSResultTableFromCSV,ResultCSVPath]=readJMAGWholeResultTables(FqfilterName);
% AppNumStudies=len(parsedMSResultTableFromCSV);
% save([defaultJEETPath,MatFileName,'.mat'],"parsedMSResultTableFromCSV")

MatFileList=findMatFiles(pwd);
MatFileList=MatFileList(contains(MatFileList,FqfilterName,"IgnoreCase",true));
MatFileList=MatFileList(~contains(MatFileList,'Fq',"IgnoreCase",true));
AppNumStudies=len(MatFileList);
PatternList={'PatternC','PatternD'};


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
    JouleAvgTablCell4Case=cell(len(speedList),2);
    speedList=zeros(1,len(tempJouleLossTableCell));
    speedNameList=cell(1,len(tempJouleLossTableCell));
    for caseIndex=1:height(tempJouleLossTableCell)
        table2Plot=tempJouleLossTableCell{caseIndex};
        tempJouleLossTable{caseIndex}        =table2Plot.Total;
        speedList(caseIndex)=freqE2rpm(1/seconds(table2Plot.Time(121)),4);
        speedNameList{1,caseIndex}=['case',num2str(caseIndex),'speed',num2str(speedList(caseIndex))];
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

formatterFigure4Paper('double','2x2')
tempx=[4000
7000
10000
13000
16000]
tempY=[
7655.81467906
12563.3254565
18711.6556516
25652.3650269
33092.5097221]
figure(2)
plot(tempx,tempY/1000,'--','DisplayName','MQS TS-FEA PatternD')

%% surface plot AC Loss TS-FEA MQS per speed

curStudyObj=app.GetCurrentStudy
ParameterListTable=getJMAGDesingTable(curStudyObj);
iph          =ParameterListTable.("Equation parameters: Ipk")
phaseAdvance =ParameterListTable.("Equation parameters: MCADPhaseAdvance")
speed =unique((ParameterListTable.("Equation parameters: speed")))


%% Correction With FQ