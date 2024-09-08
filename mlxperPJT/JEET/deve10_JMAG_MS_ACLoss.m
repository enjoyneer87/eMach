%%
'Z:\01_Codes_Projects\git_fork_emach\mlxperPJT\JEET\e10MS.m'
'Z:\01_Codes_Projects\git_fork_emach\mlxperPJT\JEET\e10.m'


% B
'Z:\01_Codes_Projects\git_fork_emach\mlxperPJT\JEET\devSettingBcontour.m'
'Z:\01_Codes_Projects\git_fork_emach\mlxperPJT\JEET\devSettingAcontour.m'


%% WaveForm

devSettingProbeB
devSettingProbeJ
devSettingProbeJouleLoss

%% GetData N Parsing
%% -Get Data
probeBFilePath=findCSVFiles(pwd)';
PJTName     ='MS';
BoolPJTName=1;
BoolRef=1;
BoolPJTName =contains(probeBFilePath,PJTName,'IgnoreCase',true);
% BoolRef     =~contains(probeBFilePath,'ref','IgnoreCase',true)
BoolLoad    =contains(probeBFilePath,'_Load','IgnoreCase',true);
BoolProbeB  =contains(probeBFilePath,'ProbeB','IgnoreCase',true);
BoolLossByJ =contains(probeBFilePath,'LossByJ','IgnoreCase',true);

MSProbeCSVPath=probeBFilePath(BoolPJTName&BoolLoad&BoolProbeB&BoolRef);

YLimitRange=[-0.4 0.4];
YLabelName ='B[T]';
MSRMSesultTableFromCSV=cell(length(MSProbeCSVPath),3);
MSRMSesultTableFromCSV=cell2table(MSRMSesultTableFromCSV);
MSRMSesultTableFromCSV.Properties.VariableNames={'ResultTable','CSVPath','Name4Mat'};
for CSVIndex=1:length(MSProbeCSVPath)
    opts=delimitedTextImportOptions('NumVariables',1000);
    if exist(MSProbeCSVPath{CSVIndex},"file")  % CSV File 존재시
    [FileDir,DataNameByCSVName,~]           =fileparts(MSProbeCSVPath{CSVIndex});
    parsedMatFilePath=fullfile(FileDir,[DataNameByCSVName,'.mat']);
        if ~exist(parsedMatFilePath,"file") %있으면 불러오지말기
            tempRawTable                            =readtable(MSProbeCSVPath{CSVIndex},opts);
            tempRawTable.Properties.Description     =DataNameByCSVName;    
            MSRMSesultTableFromCSV.CSVPath{CSVIndex}    =MSProbeCSVPath{CSVIndex};
            parsedTable                             =parseJMAGResultTable(tempRawTable);
            MSRMSesultTableFromCSV.ResultTable{CSVIndex}=parsedTable;
            MSRMSesultTableFromCSV.Name4Mat{CSVIndex}   =DataNameByCSVName;
            save(parsedMatFilePath,"parsedTable")
        else
            MSRMSesultTableFromCSV.CSVPath{CSVIndex}    =MSProbeCSVPath{CSVIndex};
            tempStruct              = load(parsedMatFilePath);
            MSRMSesultTableFromCSV.ResultTable{CSVIndex}=tempStruct.parsedTable;
            MSRMSesultTableFromCSV.Name4Mat{CSVIndex}   =DataNameByCSVName;
        end
    end
end

R4AbsPlot          =plotTransientTable(MSRMSesultTableFromCSV.ResultTable{1}.("R4_(Absolute)"){1}); 

hold on
L4AbsPlot          =plotTransientTable(MSRMSesultTableFromCSV.ResultTable{1}.("L4_(Absolute)"){1});  
ax=convertFigXAxisToElecDeg(0);
formatterFigure4Paper('double','2x2')
% Plot 2 UVW
R4AbsPlot{1}.LineStyle='--'
R4AbsPlot{1}.Marker='^'
L4AbsPlot{1}.LineStyle='-'
L4AbsPlot{1}.Marker='*'

%% By Table[WIP - ResultTable 
ResultCSVPath=exportJMAGAllCaseTables(app,'JEET');
%% Load JMAG Table
MSfilterName={'MS','_Load','ref'};
parsedMSResultTableFromCSV=readJMAGWholeResultTables(MSfilterName);
StudyIndex          =1;
TableName           =parsedMSResultTableFromCSV{StudyIndex}.Properties.Description;  % JouleLoss ActivePartaks만 회로에 넣음
%
DCJouleLossTableActive     =parsedMSResultTableFromCSV{StudyIndex}{1,"JouleLoss:W"}{:};

AllSlotsTable      =DCJouleLossTableActive(:,contains(DCJouleLossTableActive.Properties.VariableNames,'Stator'));
SumAllColumns      =sum(AllSlotsTable{:, :}, 2);
Slot6Name          ='Stator/Region';
DCGraph{1}                 =plotTransientTable(SumAllColumns); % Plot 1=DCJouleLossTableActive.Properties.VariableNames'
DCJouleLossTableSlot6      =DCJouleLossTableActive(:,contains(DCJouleLossTableActive.Properties.VariableNames,Slot6Name));
DCJouleLossWaveSlot6Active =DCJouleLossTableSlot6.(Slot6Name);
DCGraph{2}                 =plotTransientTable(DCJouleLossWaveSlot6Active); % Plot 2

OneDCLossSlotActive         =mean(DCJouleLossWaveSlot6Active);
MeanByDCLossWaveformBy6Slots=mean(DCJouleLossWaveSlot6Active(end-120:end)*6);
AbserrorFromSummAllWaveNSingleWaveMean=SumAllColumns-MeanByDCLossWaveformBy6Slots;
percenterErro=SumAllColumns/MeanByDCLossWaveformBy6Slots;
DCGraph{2}{1}.DisplayName='DCJouleLossWaveFrom1SlotToAll';
% validation with Current and RphActive
Iwaveform=parsedMSResultTableFromCSV{StudyIndex}(1,"CircuitCurrent:A");
IwaveformV=Iwaveform{1,"CircuitCurrent:A"}{1}.Coil2;
IwaveformU=Iwaveform{1,"CircuitCurrent:A"}{1}.Coil1;
IwaveformW=Iwaveform{1,"CircuitCurrent:A"}{1}.Coil3;

DCLossWaveformByIwaveVph     =IwaveformV.^2 * (RphinCircuitActive);                 %Phase DC Loss
DCLossWaveformByIwaveUph     =IwaveformU.^2 * (RphinCircuitActive);                 %Phase DC Loss
DCLossWaveformByIwaveWph     =IwaveformW.^2 * (RphinCircuitActive);                 %Phase DC Loss
DCGraph{3}=plotTransientTable(DCLossWaveformByIwaveVph);                       % Plot phase V
DCGraph{4}=plotTransientTable(DCLossWaveformByIwaveUph);                       % Plot phase V
DCGraph{5}=plotTransientTable(DCLossWaveformByIwaveWph);                       % Plot phase V
DCGraph{3}{1}.DisplayName='DCLoss Ph V';
DCGraph{4}{1}.DisplayName='DCLoss Ph U';
DCGraph{5}{1}.DisplayName='DCLoss Ph W';
AxSlot6=gca;

DCJouleTotalWave    =(DCLossWaveformByIwaveUph+DCLossWaveformByIwaveVph+DCLossWaveformByIwaveWph);
DCGraph{6}          =plotTransientTable(DCJouleTotalWave);                       % Plot 2 UVW
DCGraph{6}{1}.DisplayName='DCLoss Ph All';
AxSlot6=gca;
% Ratio
% plotTransientTable(DCJouleLossWaveSlot6Active*2./DCLossWaveformByIwave)      % Plot3


JrmsFromJmagArea                        =calcCurrentDensity(Irms,2,1,OneSlotAreaInmm2*FillFactor/4);  % Arms/mm2
JrmsFromJmagCoilContour                 =Am2_to_Amm2(18660942.448);
JrmsFromJmagCoilContourModiByFilFactor  =JrmsFromJmagCoilContour/FillFactor;
errorFromCalcJNJContourWithFillFactor   = JrmsFromJmagCoilContourModiByFilFactor-JrmsFromJmagArea  % 0.042
JrmsFromJmagCoilContourModiByFilFactor-JrmsMCAD;
OneSlotVolumninM3          =OneSlotArea*mm2m(refDimension.lactive);
DCLossin1SlotNotCorrect    = calcJLoss(JrmsFromJmagCoilContourinAMsqr, OneSlotVolumninM3, rhoJmagDefault)
DCLossin1Slot              = calcJLoss(Amm2_to_Am2(JrmsFromJmagCoilContourModiByFilFactor), OneSlotVolumninM3*FillFactor, rhoJmagDefault)
DCLoss1phFromFilFactor     = DCLossin1Slot*(slots/3)
DCLoss1Ph                  = calcDCLossByJ(JrmsFromJmagCoilContourinAMsqr,OneSlotArea,refDimension.lactive,slots,FillFactor,rhoJmagDefault)

% DCLoss1PhByIWaveForm       = rms(DCLossWaveformByIwave)  % 안맞음
% DCLoss1PhByIWaveForm       = mean(DCLossWaveformByIwave)  % 안맞음 1.4383e+03
% ErrorFromJrmsNIwaveForm    = DCLoss1Ph-DCLoss1PhByIWaveForm  % -51.5715
% MeanByDCLossWaveformByI=mean(DCLossWaveformByIwave)*3;    %% mean으로 해도 안맞음 조금큼  4.4695e+03

% By Loss Density
% DCLoss1Ph/OneSlotVolumninM3
% RMSLossJDnesityContour=122654595.257
% 
% (DCLoss1Ph*3)/(RMSLossJDnesityContour*OneSlotVolumninM3)
% 
% DCLossByRwEnd=Irms.^2*3*RphwEnd
% DCLossByRActive=Irms.^2*3*RphinCircuitActive
% MeanByDCLossWaveformByI-DCLossByRActive 
% MeanByDCLossWaveformByI-DCLoss1phFromFilFactor*3
% 
% Irms.^2*3*RphinCircuitActive-DCLoss1phFromFilFactor*3





%%--Plot what get  MSRTargetTable MSthetaTargetTable
close all
LayerIndexList=[1 2 3 4];
caseIndex=1;
grhLinIndex=0;
startFromZero=0;
lineStyleList={'--','None','None'}

% YLabelName ='Joule Loss[W]';
% YLimitRange=[-1000 10000];

linecolor ={'k','b'};  %'k'= MQS, 'b'=MS
markerList={'+' , 'o' , '*' , '.' , 'x' , 'square' , 'diamond' , 'v' , '^' , '>' , '<' , 'pentagram' , 'hexagram' , ',' , '_' };
% MSgrphLineObj=cell(height(RMSesultTableFromCSV)*width(TargetTable));
% for LayerNumIndex=1:length(LayerIndexList)
    % LayerIndex=LayerIndexList(LayerNumIndex);
    for ModelNStudyIndex=1:height(MSRMSesultTableFromCSV)
            MSTargetTable     =MSRMSesultTableFromCSV.ResultTable{ModelNStudyIndex};
            BoolAbsVar        =contains(MSTargetTable.Properties.VariableNames,'Absolute');
            BoolRVar          =contains(MSTargetTable.Properties.VariableNames,'(R)');
            % BooltanVar
            % =contains(TargetTable.Properties.VariableNames,'(θ)');
            BoolZVar          =contains(MSTargetTable.Properties.VariableNames,'(Z)');
            % ConductorIndex    =contains(MSTargetTable.Properties.VariableNames,num2str(LayerIndex));
            MSRTargetTable{ModelNStudyIndex}   =MSTargetTable(:,~BoolAbsVar&BoolRVar&~BoolZVar);  % RTable
            MSthetaTargetTable{ModelNStudyIndex}=MSTargetTable(:,~BoolAbsVar&~BoolRVar&~BoolZVar);  % theta
            % AbsTargetTable=MSTargetTable(:,BoolAbsVar&~BoolRVar&~BoolZVar&ConductorIndex);
            % MSRTargetTable=MSTargetTable(:,~BoolAbsVar&BoolRVar&~BoolZVar&ConductorIndex);  % RTable
            % MSthetaTargetTable=MSTargetTable(:,~BoolAbsVar&~BoolRVar&~BoolZVar&ConductorIndex);  % theta
            % % ABs
            % TargetTable=TargetTable(:,~BoolAbsVar&BoolRVar&~BoolZVar&ConductorIndex);
            % % R
    end
    
    % for caseIndex=1:height(TargetTable)
        % for DataIndex=1:width(TargetTable)
        for DataIndex=1:2
            figure(ModelNStudyIndex)
            tempTargetTable=MSTargetTable{caseIndex,DataIndex}{:};
            tempTargetTable=tempTargetTable(end-120:end,:);
            tempTargetTable.Variables=tempTargetTable.Variables;
            MSgrphLineObj(grhLinIndex+1)=plotTransientTable(tempTargetTable);
            PJTModelName=strsplit(MSRMSesultTableFromCSV.Name4Mat{ModelNStudyIndex},'_');
            PJTModelName=strrep(PJTModelName,'MQS','MQS ');
            PJTModelName=strrep(PJTModelName,'MS','MS ');
            curDispName=MSgrphLineObj{grhLinIndex+1}.DisplayName;
            curDispName=strrep(curDispName,' ','');
            curDispName=strsplit(curDispName,'(');
            curDispName=curDispName{1};
            NeweName=[PJTModelName{1},' ',curDispName];
            MSgrphLineObj{grhLinIndex+1}.DisplayName=NeweName;
            BoolR=~(DataIndex-1);
            if contains(PJTModelName{1},'MS')
                linecolor=[0 114 189]/256+(DataIndex-1)*60/256;
                BoolMQS=0;
                MSgrphLineObj{grhLinIndex+1}.MarkerFaceColor=linecolor;
            else
                linecolor=[217, 83, 25]/256+(DataIndex-1)/2*60/256;
                BoolMQS=1;
            end
            MSgrphLineObj{grhLinIndex+1}.Color=linecolor;
         
            if ~BoolR
                LineStyle='--';
            elseif BoolR&~BoolMQS
                LineStyle='-';
            elseif BoolR&BoolMQS
                LineStyle='None';
            end
    
            if contains(PJTModelName{1},'ref')
            MSgrphLineObj{grhLinIndex+1}.Marker         ='o';
            else
            MSgrphLineObj{grhLinIndex+1}.Marker     ='^';
            end
            MSgrphLineObj{grhLinIndex+1}.LineWidth=2;
            MSgrphLineObj{grhLinIndex+1}.LineStyle=LineStyle;
            %%
            CurDuration=MSgrphLineObj{grhLinIndex+1}.XData(end)-MSgrphLineObj{grhLinIndex+1}.XData(1);
            xTicks = 0:3:360;
            timeTicks = startFromZero+ (xTicks / 360) * CurDuration;   
            MSgrphLineObj{grhLinIndex+1}.XData=seconds(timeTicks);
            ax=convertFigXAxisToElecDeg(0);
            ylabel(ax, YLabelName);
            ax.XLim=[timeTicks(1) timeTicks(end)];
            % grphLineObj{1}.Marker='*'l
            ax.YLim=YLimitRange;
            hold on
            grhLinIndex=grhLinIndex+1;
            formatterFigure4Paper('Double','2x2');
        end
    % end
    % end
% end 
%% Hybrid Calc
refDim=[3.7/2 1.6 150]
pole=8
speedList=[1000:2000:13000];
refDim(3)=150
% DCLossWaveformByIwaveVph from deve10_Comparison_MQS_MS line 75
% close all
clear meanLineMS
for ModelNStudyIndex=2:2
    for speedIndex=1:6
        speed=speedList(speedIndex);
        [TotalACLossPerMethod{speedIndex},TotalDCACSlot{speedIndex},DisplaynameList,meanLineMS{speedIndex}]=calcAllHybridACFromBtable(speed,pole,refDim,MSRTargetTable{ModelNStudyIndex}(1,:),MSthetaTargetTable{ModelNStudyIndex}(1,:),3*DCLossWaveformByIwaveVph);
    end    
end

SCDim=2*refDim
SCDim(3)=150

for ModelNStudyIndex=2:2
    for speedIndex=1:6
        speed=speedList(speedIndex);
        [SCTotalACLossPerMethod{speedIndex},TotalDCACSlot{speedIndex},DisplaynameList,SCACmeanLineMS{speedIndex}]=calcAllHybridACFromBtable(speed,pole,SCDim,MSRTargetTable{ModelNStudyIndex}(1,:),MSthetaTargetTable{ModelNStudyIndex}(1,:),3*DCLossWaveformByIwaveVph);
    end    
end

smallDim=0.5*refDim;
smallDim(3)=150
for ModelNStudyIndex=2:2
    for speedIndex=1:6
        speed=speedList(speedIndex);
        [smallSCTotalACLossPerMethod{speedIndex},TotalDCACSlot{speedIndex},DisplaynameList,SmallACmeanLineMS{speedIndex}]=calcAllHybridACFromBtable(speed,pole,smallDim,MSRTargetTable{ModelNStudyIndex}(1,:),MSthetaTargetTable{ModelNStudyIndex}(1,:),3*DCLossWaveformByIwaveVph);
    end    
end

for ModelNStudyIndex=2:2
    for speedIndex=1:6
        speed=4*speedList(speedIndex);
        [TotalACLossPerMethod{speedIndex},TotalDCACSlot{speedIndex},DisplaynameList,ScaleSpeedmeanLineMS{speedIndex}]=calcAllHybridACFromBtable(speed,pole,refDim,MSRTargetTable{ModelNStudyIndex}(1,:),MSthetaTargetTable{ModelNStudyIndex}(1,:),3*DCLossWaveformByIwaveVph);
    end    
end

%%
% close all

%% Joule Loss Density
% bupTable=ResultTableFromCSV

YLimitRange=[0 1*10e7/1000];
YLabelName ='Loss Density[kW/m^{3}]';

probeBFilePath=findCSVFiles(pwd)';
BoolPJTName=1;
BoolRef=1;
PJTName='MS'
BoolPJTName =contains(probeBFilePath,PJTName,'IgnoreCase',true)
% BoolRef     =~contains(probeBFilePath,'ref','IgnoreCase',true)
BoolLoad    =contains(probeBFilePath,'_Load','IgnoreCase',true);
BoolProbeB  =contains(probeBFilePath,'ProbeB','IgnoreCase',true);
BoolLossByJ =contains(probeBFilePath,'LossByJ','IgnoreCase',true);


MSProbeCSVPath=probeBFilePath(BoolPJTName&BoolLoad&BoolLossByJ&BoolRef);
MSRMSesultTableFromCSV=cell(length(MSProbeCSVPath),3);
MSRMSesultTableFromCSV=cell2table(MSRMSesultTableFromCSV);
MSRMSesultTableFromCSV.Properties.VariableNames={'ResultTable','CSVPath','Name4Mat'};
% ResultTableFromCSV=ResultTableFromCSV(contains(ResultTableFromCSV.Name4Mat,'MS'),:)
for CSVIndex=1:length(MSProbeCSVPath)
    opts=delimitedTextImportOptions('NumVariables',1000);
    if exist(MSProbeCSVPath{CSVIndex},"file")  % CSV File 존재시
    [FileDir,DataNameByCSVName,~]           =fileparts(MSProbeCSVPath{CSVIndex});
    parsedMatFilePath=fullfile(FileDir,[DataNameByCSVName,'.mat']);
        if ~exist(parsedMatFilePath,"file") %있으면 불러오지말기
            tempRawTable                            =readtable(MSProbeCSVPath{CSVIndex},opts);
            tempRawTable.Properties.Description     =DataNameByCSVName;    
            MSRMSesultTableFromCSV.CSVPath{CSVIndex}    =MSProbeCSVPath{CSVIndex};
            parsedTable                             =parseJMAGResultTable(tempRawTable);
            MSRMSesultTableFromCSV.ResultTable{CSVIndex}=parsedTable;
            MSRMSesultTableFromCSV.Name4Mat{CSVIndex}   =DataNameByCSVName;
            save(parsedMatFilePath,"parsedTable")
        else
            MSRMSesultTableFromCSV.CSVPath{CSVIndex}    =MSProbeCSVPath{CSVIndex};
            tempStruct              = load(parsedMatFilePath);
            MSRMSesultTableFromCSV.ResultTable{CSVIndex}=tempStruct.parsedTable;
            MSRMSesultTableFromCSV.Name4Mat{CSVIndex}   =DataNameByCSVName;
        end
    end
end



%%--Plot
close all
LayerIndex=[4 3];
caseIndex=1;
grhLinIndex=0;
startFromZero=0;
lineStyleList={'--','None','None'}

linecolor ={'k','b'};  %'k'= MQS, 'b'=MS
markerList={'+' , 'o' , '*' , '.' , 'x' , 'square' , 'diamond' , 'v' , '^' , '>' , '<' , 'pentagram' , 'hexagram' , ',' , '_' };
MSgrphLineObj=cell(height(MSRMSesultTableFromCSV)*width(MSTargetTable));
for LayerIndex=3:4
    for ModelNStudyIndex=1:height(MSRMSesultTableFromCSV)
            MSTargetTable=MSRMSesultTableFromCSV.ResultTable{ModelNStudyIndex};
            BoolAbsVar        =contains(MSTargetTable.Properties.VariableNames,'Absolute');
            BoolRVar          =contains(MSTargetTable.Properties.VariableNames,'(R)');
            % BooltanVar
            % =contains(TargetTable.Properties.VariableNames,'(θ)');
            BoolZVar          =contains(MSTargetTable.Properties.VariableNames,'(Z)');
            ConductorIndex    =contains(MSTargetTable.Properties.VariableNames,num2str(LayerIndex));
            MSTargetTable=MSTargetTable(:,~BoolAbsVar&~BoolRVar&~BoolZVar&ConductorIndex);  % theta
            % TargetTable=TargetTable(:,BoolAbsVar&~BoolRVar&~BoolZVar&ConductorIndex);
            % % ABs
            % TargetTable=TargetTable(:,~BoolAbsVar&BoolRVar&~BoolZVar&ConductorIndex);
            % % R
    % for caseIndex=1:height(TargetTable)
        % for DataIndex=1:width(TargetTable)
        for DataIndex=1:2
            figure(LayerIndex)
            tempTargetTable=MSTargetTable{caseIndex,DataIndex}{:};
            tempTargetTable=tempTargetTable(end-120:end,:);
            tempTargetTable.Variables=tempTargetTable.Variables/1000;
            MSgrphLineObj(grhLinIndex+1)=plotTransientTable(tempTargetTable.Variables);
            PJTModelName=strsplit(MSRMSesultTableFromCSV.Name4Mat{ModelNStudyIndex},'_');
            PJTModelName=strrep(PJTModelName,'MQS','MQS ');
            PJTModelName=strrep(PJTModelName,'MS','MS ');
            curDispName=MSgrphLineObj{grhLinIndex+1}.DisplayName;
            curDispName=strrep(curDispName,' ','');
            curDispName=strsplit(curDispName,'(');
            curDispName=curDispName{1};
            NeweName=[PJTModelName{1},' ',curDispName];
            MSgrphLineObj{grhLinIndex+1}.DisplayName=NeweName;
            BoolR=~(DataIndex-1);
            if contains(PJTModelName{1},'MS')
                linecolor=[0 114 189]/256+(DataIndex-1)*60/256;
                BoolMQS=0;
                MSgrphLineObj{grhLinIndex+1}.MarkerFaceColor=linecolor;
            else
                linecolor=[217, 83, 25]/256+(DataIndex-1)/2*60/256;
                BoolMQS=1;
            end
            MSgrphLineObj{grhLinIndex+1}.Color=linecolor;
         
            if ~BoolR
                LineStyle='--';
            elseif BoolR&~BoolMQS
                LineStyle='-';
            elseif BoolR&BoolMQS
                LineStyle='None';
            end
    
            if contains(PJTModelName{1},'ref')
            MSgrphLineObj{grhLinIndex+1}.Marker         ='o';
            else
            MSgrphLineObj{grhLinIndex+1}.Marker     ='^';
            end
            MSgrphLineObj{grhLinIndex+1}.LineWidth=2;
            MSgrphLineObj{grhLinIndex+1}.LineStyle=LineStyle;
            %%
            % CurDuration=grphLineObj{grhLinIndex+1}.XData(end)-grphLineObj{grhLinIndex+1}.XData(1);
            % xTicks = 0:3:360;
            % timeTicks = startFromZero+ (xTicks / 360) * CurDuration;   
            % grphLineObj{grhLinIndex+1}.XData=seconds(timeTicks);
            ax=convertFigXAxisToElecDeg(0);
            ylabel(ax, YLabelName);
            % ax.XLim=[timeTicks(1) timeTicks(end)];
            % grphLineObj{1}.Marker='*'l
            ax.YLim=YLimitRange;
            hold on
            grhLinIndex=grhLinIndex+1;
            formatterFigure4Paper('Double','2x2');
        end
    % end
    end
end
%% 
%% MS DC Loss From deve10_Comparison
mcad=callMCAD;

Irms             =460;
rhoMCAD          =1.724E-08;
rhoJmagDefault   =1.673e-08;
rhoJmagDefault/rhoMCAD;
ParallelNumber   =2;
JrmsFromJmagCoilContourinAMsqr=18660942.448;
OneSlotAreaInmm2      =49.3540707449101;
OneSlotArea=(mm2m(mm2m(49.3540707449101)));
curFilePath=getMCADFilePathCurrent(mcad);
MotorGeo=getMCADData4ScalingFromMotFile(curFilePath);
pole=MotorGeo.MotorCADGeo.Pole_Number;
slots=MotorGeo.MotorCADGeo.Slot_Number;


RphinCircuitActive=MotorGeo.MotorCADGeo.ResistanceActivePart;
RphwEnd          =0.01084;
NStrand             =MotorGeo.MotorCADGeo.NumberStrandsHand;
ArmatureConductorCSA=MotorGeo.MotorCADGeo.ArmatureConductorCSA  % ArmatureConductorCSA= The cross sectional area of the armature conductor
copperArea          =ArmatureConductorCSA*4
FillFactor          =copperArea/OneSlotAreaInmm2
JrmsMCAD            =calcCurrentDensity(Irms,2,NStrand,ArmatureConductorCSA); 
NSPP=calcNSPP(slots,MotorGeo.MotorCADGeo.Pole_Number)
refDimension.w=3.7;
refDimension.h=1.6;
refDimension.lactive=150;
refDimension.w*refDimension.h;


%% dev pre MS Joule Loss
tempJouleLossTable=tempCellResultTableFromCSV{1}.("JouleLoss:W"){caseIndex(1)}
PartNameList      =tempJouleLossTable.Properties.VariableNames';
WirePartName='Wire'
SlotWirePartName  =PartNameList(contains(PartNameList,WirePartName,'IgnoreCase',true));
if ~isempty(SlotWirePartName)
    disp(['도체이름은 "',WirePartName,'"'])
end
grhLinIndex=0;
LineStyle='--'
YLabelName ='Joule Loss[W]';
YLimitRange=[-1000 5000];
% for speedIndex=1:3:length(speedList)
for speedIndex=6:6
    for LayerNumIndex=1:len(LayerIndexList)
        for SlotIndex=1:len(SlotIndexList)
            for PJTNameIndex=1:len(PJTNameList)
                % for ModelNameIndex=1:len(ModelNameList)
                for ModelNameIndex=2:2
                    tempResultTable=MQSResultTableFromCSV.ResultTable{ModelNameIndex};
                    PJTModelNStudyName4Bool=tempResultTable.Properties.Description;
                    %% Bool Table
                    BoolPJTName   =contains(PJTModelNStudyName4Bool,PJTNameList{PJTNameIndex},'IgnoreCase',true);
                    BoolModelName =contains(PJTModelNStudyName4Bool,ModelNameList{ModelNameIndex},'IgnoreCase',true);
                    if BoolPJTName&&BoolModelName
                        tempResultTable=MQSResultTableFromCSV.ResultTable{ModelNameIndex};
                    else
                        continue
                    end
                    curJouleLossTable=tempResultTable.("JouleLoss:W"){speedIndex};
                    speed=freqE2rpm(1/seconds(curJouleLossTable.Time(121)),pole/2);
                    % if ~checkRPM
                    %    disp('rpm이 다릅니다')
                    %    continue
                    % end
                    curPartNameList   =curJouleLossTable.Properties.VariableNames;
                    % Bool Table VarNmae
                    BoolSlot      =contains(curPartNameList,['Slot',num2str(SlotIndexList(SlotIndex))],"IgnoreCase",true);
                    BoolWireNumber=contains(curPartNameList,['Wire',num2str(LayerIndexList(LayerNumIndex))],"IgnoreCase",true);
                    % Plot 
                    figure(speedIndex)
                    tempTargetTable=curJouleLossTable(end-120:end,BoolWireNumber&BoolSlot);
                    % OnlyAcLossArray=tempTargetTable.Variables-DCLossPerLayer;
                    % grphLineObj(grhLinIndex+1)=plotTransientTable(OnlyAcLossArray);
                    grphLineObj(grhLinIndex+1)=plotTransientTable(tempTargetTable.Variables);
                    curName=grphLineObj{grhLinIndex+1}.DisplayName;
                    NewName=[ModelNameList{ModelNameIndex},' ',curName,'@',num2str(speed)];
                    grphLineObj{grhLinIndex+1}.DisplayName=NewName;
                    hold on
                    % Color
                    if contains(PJTModelNStudyName4Bool,'MS')
                    linecolor=[0 114 189]/256+(PJTNameIndex-1)*60/256;
                    BoolMQS=0;
                    grphLineObj{grhLinIndex+1}.MarkerFaceColor=linecolor;
                    else
                        linecolor=[217, 83, 25]/256+(PJTNameIndex-1)/2*60/256;
                        BoolMQS=1;
                    end
                    grphLineObj{grhLinIndex+1}.Color=linecolor;
                    if contains(PJTModelNStudyName4Bool,'ref')
                    grphLineObj{grhLinIndex+1}.Marker         ='o';
                    else
                    grphLineObj{grhLinIndex+1}.Marker     ='^';
                    end
                    grphLineObj{grhLinIndex+1}.LineWidth=2;
                    grphLineObj{grhLinIndex+1}.LineStyle=LineStyle;
                     ax=convertFigXAxisToElecDeg(0);
                     % grphLineObj{1}.Marker='*'l
                     ax.YLim=YLimitRange;
                     ylabel(ax, YLabelName);
                     formatterFigure4Paper('Double','2x2');
                     grhLinIndex=grhLinIndex+1;        
                end % 1st Model  - ref, sc 
            end     %PJT         - MQS
        end         %Slot        - 6 
    end             %LayerNumber%  - 4 3
end                 %Speed (Case)  -7


%% Backup
% ResultCSVPath=exportJMAGAllCaseTables(app,ProjName)
ResultCSVPath=exportJMAGAllCaseTables(app,'JEET');
MSfilterName={'MS','_Load_'};
parsedMSResultTableFromCSV=readJMAGWholeResultTables(MSfilterName);
Iwaveform=parsedMSResultTableFromCSV{1}(1,"CircuitCurrent:A")
parsedMSResultTableFromCSV{1}{1,"JouleLoss:W"}{:}
Iwaveform=Iwaveform{1,"CircuitCurrent:A"}{1}.Coil1
%%
OneSlotArea=(mm2m(mm2m(49.3540707449101)));
% 
RphinCircuitActive=0.007;
RphTotal          =0.01084;
DCLossByR=(460).^2*3*RphinCircuit
DCLossWaveform =Iwaveform.^2 * (RphinCircuitActive)
mean(DCLossWaveform)*3
plot(DCLossWaveform)
(460/2)^2*RphinCircuit*2*2
1146*2
%%  LossDensity
4443.6-DCLossByR
myCalcLossDen=DCLossByR/(OneSlotArea*mm2m(150)*6)
% JMAGDCLossDen=1e8
JMAGDCLossDen=mean(tempTargetTable.Variables)*1000 % W/m^3
JMAGDCLossDen/myCalcLossDen
%% By Density
DCLossWaveformMean=(460)^2*0.01084;
DCLoss=mean(tempTargetTable.Variables)*1000*mm2m(150)*6*0.63;
DCLoss/1000

%% 
DCLossByR/DCLoss

1.866e7*mm2m(mm2m(49.3540707449101))*0.65;



%% getMeshData
PartStruct=getJMAGDesignerPartStruct(app);

idx=findMatchingIndexInStruct(PartStruct,'Name','Stator')
WireStruct=PartStruct(idx);

%% Get Wire Element and Node ID
for Index=1:length(WireStruct)
    WireIndex=WireStruct(Index).partIndex;
    [WireStruct(Index).ElementId, WireStruct(Index).NodeID]=devgetMeshData(app,WireIndex)
end

% WireStruct = updatePartStructWithFieldTable(WireStruct, BxTimeinRow, 'BxTimeinRow')




MPToolCSVFilePath='Z:/Simulation/JEETACLossValid_e10_v24/refModel/ExportMPtools/MSField.csv'
keyword='11005'; % MVP
% keyword='16001'; % B
FieldData_perStep = extractJMAGFieldVectorFromMPtoolCSV(MPToolCSVFilePath, keyword);
A=FieldData_perStep.(stepNameList{i}).vecz;
FieldData_perStep.step1.PosX

[model,pdeTriElements,pdeNodes,pdeQuadElements]  = nastran2PDEMesh(MPToolCSVFilePath);
MeshPDEtoolForm=model.Mesh;
[PetFor.p,PetFor.e,PetFor.t]=MeshPDEtoolForm.meshToPet();
PetFor.t(4,:)=[]
msh=PetFor
x = pdeNodes(1,:);
y = pdeNodes(2,:);

% 플로팅
figure;
pdemesh(model)
hold on
view(3)
quadmesh(pdeQuadElements, x, y);
centerAllFigures
NodePosX=Az.PosX;
NodePosY=Az.PosX;
NodePosZ=Az.PosZ;

for Index=1:length(WireStruct)
    nodeIDArray = str2double(Az.NodeID);
    targetNodeIDs = WireStruct(Index).NodeID;
    matchingIndices = findMatchingIndicesArray(nodeIDArray, targetNodeIDs);

    quiverWithFieldTableinPartStruct(WireStruct,PartIndex)
    hold on
end
% 
% A=FieldData_perStep.(stepNameList{i}).vecz;
% 
% stepNameList=fieldnames(FieldData_perStep)
% for i=60:1:60
% % A=Az{:,i}
% % figure(i)
% % [p_plot, plotArgs] = aux_Plotting_parseInput(msh);
% t = msh.t;
% I = 1;
% 
% % drawFluxDensity(msh, A); 
% end