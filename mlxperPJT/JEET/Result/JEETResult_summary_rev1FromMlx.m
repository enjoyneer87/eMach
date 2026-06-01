
SpeedList=[1000:1000:20000];
delta=calcSkinDepth(omega2freq(rpm2OmegaE(SpeedList,4))) % 2.25594 -
delta=calcSkinDepth(omega2freq(rpm2OmegaE(20000,4))) % 2.25594 -
1.6/2.86
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
plot(SpeedList, skin_depth*0.5);
xlabel('Rotational Speed[RPM]');
ylabel('Skin Depth (mm)');
title('Skin Depth vs RPM');
grid on;

skinDepthList=[SpeedList,skin_depth]

%%
markerList={'+' , 'o' , '*' , '.' , 'x' , 'square' , 'diamond' , 'v' , '^' , '>' , '<' , 'pentagram' , 'hexagram' , ',' , '_' };

%% Juha

% close all
rpPlotJuhaAC

%% plot3DVectorB 

% dev_plot3DVectorB_4ExportMVP_Mesh_SHmethod

% D:\KangDH\Emlab_emach\mlxperPJT\JEET\rpREFMSBfield.m
%% case 28 - 460.1 @45deg
rpREFTSBfield
rpREFMSBfield
load('REF_TS_18krpm_case28_Mesh.mat')
figure(1)
[TaS,Tview,Tratio]=lockAxisAndView
hold on
plotJMAGMesh(TSMesh)
ax=gca;
restoreView(ax, TaS,Tview,Tratio)
legend
figure(3)
[RaS,Rview,Rratio]=lockAxisAndView
plotJMAGMesh(TSMesh)
ax=gca;
restoreView(ax,RaS,Rview,Rratio)
rp4BMergeFigures
%% SCL
rpSCLTSBfield
rpSCLMSBfield
load('SCL_TS_18krpm_case28_Mesh.mat')
load('SCL_MS_18krpm_case28_Mesh.mat')
figure(1)
[TaS,Tview,Tratio]=lockAxisAndView
hold on
plotJMAGMesh(SCL_MSMesh)
ax=gca;
restoreView(ax, TaS,Tview,Tratio)
legend
figure(3)
[RaS,Rview,Rratio]=lockAxisAndView
plotJMAGMesh(SCL_TSMesh)
ax=gca;
restoreView(ax,RaS,Rview,Rratio)
rp4BMergeFigures
%% Fatami Interp

devdelauytri
devFieldGridInterp
%% Jmag HYB -Prox

dev
rpPlotAllHYB
% SCL FQ

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
for AppStudyIndex=1:AppNumStudies
    load(MatFileListFq{AppStudyIndex})
    tempJouleLossTableCell=parsedResultTable5StudyPerStudy.("JouleLoss:W");
    for caseIndex=1:height(tempJouleLossTableCell)
        tempJouleLossTable{caseIndex}        =tempJouleLossTableCell{caseIndex}.Total;
        freqEList=tempJouleLossTableCell{caseIndex}.Properties.RowNames;
        RPMList=freq2rpm(elec2mech(convertCharCell2Numeric(freqEList),4))
    end
    for tableIndex=1:1
        plot2Table=tempJouleLossTable{tableIndex};
        if contains(MatFileListFq{AppStudyIndex},'SCL','IgnoreCase',true)
        figure(2)
        linesty=LineList{2}
        DispName='SCL'
        elseif contains(MatFileListFq{AppStudyIndex},'ref','IgnoreCase',true)
        figure(1)
        linesty=LineList{1}
        DispName='REF'
        end
        plot(RPMList,plot2Table/1000,'DisplayName','FQ')
        title(DispName)
        hold on
    end
end

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

%%
curStudyObj=app.GetCurrentStudy
ParameterListTable=getJMAGDesingTable(curStudyObj);
iph          =ParameterListTable.("Equation parameters: Ipk")
phaseAdvance =ParameterListTable.("Equation parameters: MCADPhaseAdvance")
speed =unique((ParameterListTable.("Equation parameters: speed")))

% rpACLossdqSurf.mlx - 
% 1) surface plot AC Loss TS-FEA MQS per speed
% 2) speed plot per Ipk Phase Advance

rpACLossdqSurf.mlx
%% Plot With var Method
% continue with 2)

% open("Comp_TotalMaxIpkPerSpeed.fig")
PhaseAdvance= 43.3
tempIsrms=460;
close all
% FigFileName=['Comp_SameIpkPerSpeed',strrep(num2str(PhaseAdvance),'.','_'),num2str(tempIsrms)];
FigFileName=['Comp_SameSatuPerSpeed',strrep(num2str(PhaseAdvance),'.','_'),num2str(tempIsrms)];
open([FigFileName,'.fig'])
open('REF_ACvaryMethod.fig')
% savefig(figure(1),"REF_ACvaryMethod_R1.fig")
% open("SCLvaryMethod.fig")
savefig(figure(2),"SCLvaryMethod_R1.fig")
open("SCLvaryMethod_R1.fig")
open("REF_ACvaryMethod_R1.fig")

open("D:\KangDH\Emlab_emach\mlxperPJT\JEET\From38100\JuhaCalc.fig")
%% MQSMergedSCLvaryMethod_R1
mergeFigures([1 2 ])
view(2)
formatterFigure4Paper('double','2x2')
grid on
savefig(gcf,"MQSMergedSCLvaryMethod_R1.fig")
savefig(gcf,"MQSMergedSREFvaryMethod_R1.fig")

%%
open("MQSMergedSCLvaryMethod_R1.fig")
figAx=figure(7).Children(2)
figAx.YLim=[0 10]
mergeFigures([4 3])
view(2)
setlegendBoxShape(2)

% ratio

lineobj=findobj(figure(2),'Type','line')
addString='REF'
for LineIndex=1:len(lineobj)
    % lineXDataList{LineIndex}=lineobj(LineIndex).XData
    % lineYDataList{LineIndex}=lineobj(LineIndex).YData
    linelegend{LineIndex}=lineobj(LineIndex).Parent.Legend.String{LineIndex};
    lineobj(LineIndex).Parent.Legend.String{LineIndex}=[linelegend{LineIndex} ,':',addString]
end

savefig(figure(1),"tempSCL.fig")
savefig(figure(2),"tempREF.fig")
open("tempSCL.fig")
open("tempREF.fig")

mergeFigures([1 2])
view(2)

lineobj=findobj(gcf,'Type','line')
for LineIndex=1:len(lineobj)
    lineXDataList{LineIndex}=lineobj(LineIndex).XData
    lineYDataList{LineIndex}=lineobj(LineIndex).YData
    linelegend{LineIndex}=lineobj(LineIndex).Parent.Legend.String{LineIndex};
end

tol=1e-6
len(lineXDataList{1})==len(lineXDataList{2})

for LineIndex=1:len(lineobj)
[fitFun{LineIndex}.fitresult, fitFun{LineIndex}.gof] = polyFitCurve(lineXDataList{LineIndex}, lineYDataList{LineIndex}, 5)
end

mergeFigures([2 3])
view(2)
f1=fitFun{1}.fitresult(1:1:20)
f2=fitFun{2}.fitresult(1:1:20)
hold on
plot([1:20],f1./f2)
%% Plot Only HYB SCL/REF AC Ratio
lineobj=findobj(gcf,'Type','line')
for LineIndex=1:len(lineobj)
    lineobj(LineIndex).YData=lineobj(LineIndex).YData-DCLoss/1000
    % figAx=figure(figureIndex).Children(2)
    % figAx.XLim=[0 20]
end

lineobj=findobj(gcf,'Type','line')
for LineIndex=1:len(lineobj)
    lineXDataList{LineIndex}=lineobj(LineIndex).XData
    lineYDataList{LineIndex}=lineobj(LineIndex).YData
    linelegend{LineIndex}=lineobj(LineIndex).Parent.Legend.String{LineIndex};
end



for LineIndex=1:len(lineobj)
[fitFun{LineIndex}.fitresult, fitFun{LineIndex}.gof] = polyFitCurve(lineXDataList{LineIndex}, lineYDataList{LineIndex}, 5)
end

mergeFigures([2 3])
view(2)
f1=fitFun{1}.fitresult(1:1:20)
f2=fitFun{2}.fitresult(1:1:20)
% figure(1)
hold on
plot([1:20],f1./f2)
savefig(gcf,"tempHYB2DG2_SCLREFACRatio.fig")

% Plot Only RECT HYB N TS R1

close all
open("Comp_TotalMaxIpkPerSpeed.fig")
open("REF_AC.fig")
open("SCL_AC.fig")
for figureIndex=1:1
    lineobj=findobj(figure(figureIndex),'Type','line')
for LineIndex=1:len(lineobj)
    lineobj(LineIndex).XData=lineobj(LineIndex).XData/1000
    figAx=figure(figureIndex).Children(2)
    figAx.XLim=[0 20]
end
end

mergeFigures([2 1])
view(2)
formatterFigure4Paper('double','2x2')
grid on
setlegendBoxShape(3)
figAx=figure(4).Children(2)
figAx.YLim=[4 10]
%% Plot 3D J with Mesh

D:\KangDH\Emlab_emach\mlxperPJT\JEET\dev4Summary_Plot3DJMesh.m
% Correction With FQ