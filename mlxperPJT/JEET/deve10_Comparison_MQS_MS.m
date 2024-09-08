deve10_Comparison_MQS_MS


Z:\01_Codes_Projects\git_fork_emach\mlxperPJT\JEET\e10MS.m
Z:\01_Codes_Projects\git_fork_emach\mlxperPJT\JEET\e10.m
Z:\01_Codes_Projects\git_fork_emach\mlxperPJT\JEET\deve10_JMAG_MS_ACLoss.m



Z:\01_Codes_Projects\git_fork_emach\mlxperPJT\JEET\e10MQS_WireTemplate.m
Z:\01_Codes_Projects\git_fork_emach\mlxperPJT\JEET\deve10_JMAG_MQS_ACLoss.m
Z:\01_Codes_Projects\git_fork_emach\mlxperPJT\deve10MQSplotAC.m


setTextFontSize(allFigures(1), 25)
%% AC Loss Plot - 
%% MS DC Loss

Irms             =460;
rhoMCAD          =1.724E-08;
rhoJmagDefault   =1.673e-08;
rhoJmagDefault/rhoMCAD;
ParallelNumber   =2;
JrmsFromJmagCoilContourinAMsqr=18660942.448;
OneSlotAreaInmm2      =49.3540707449101;
OneSlotArea=(mm2m(mm2m(49.3540707449101)));
mcad=callMCAD;
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

%% By Table[WIP - ResultTable
% ResultCSVPath=exportJMAGAllCaseTables(app,'JEET');

MSfilterName={'MS','_Load_'};
parsedMSResultTableFromCSV=readJMAGWholeResultTables(MSfilterName);
TableName=parsedMSResultTableFromCSV{1}.Properties.Description  % JouleLoss ActivePartaks만 회로에 넣음
%
DCJouleLossTableActive     =parsedMSResultTableFromCSV{1}{1,"JouleLoss:W"}{:};

AllSlotsTable      =DCJouleLossTableActive(:,contains(DCJouleLossTableActive.Properties.VariableNames,'Stator'))
SumAllColumns      =sum(AllSlotsTable{:, :}, 2);
DCGraph{1}                 =plotTransientTable(SumAllColumns) % Plot 1

DCJouleLossTableSlot6      =DCJouleLossTableActive(:,contains(DCJouleLossTableActive.Properties.VariableNames,'Region.2_5'))
DCJouleLossWaveSlot6Active =DCJouleLossTableSlot6.("Stator/Region.2_5")
DCGraph{2}                 =plotTransientTable(DCJouleLossWaveSlot6Active) % Plot 2

OneDCLossSlotActive         =mean(DCJouleLossWaveSlot6Active)
MeanByDCLossWaveformBy6Slots=mean(DCJouleLossWaveSlot6Active(end-120:end)*6);
AbserrorFromSummAllWaveNSingleWaveMean=SumAllColumns-MeanByDCLossWaveformBy6Slots;
percenterErro=SumAllColumns/MeanByDCLossWaveformBy6Slots;
DCGraph{2}{1}.DisplayName='DCJouleLossWaveFrom1SlotToAll';
% validation with Current and RphActive
Iwaveform=parsedMSResultTableFromCSV{1}(1,"CircuitCurrent:A");
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

DCJouleTotalWave=(DCLossWaveformByIwaveUph+DCLossWaveformByIwaveVph+DCLossWaveformByIwaveWph)
DCGraph{6}=plotTransientTable(DCJouleTotalWave);                       % Plot 2 UVW
DCGraph{6}{1}.DisplayName='DCLoss Ph All';
AxSlot6=gca;
% Ratio
% plotTransientTable(DCJouleLossWaveSlot6Active*2./DCLossWaveformByIwave)      % Plot3


JrmsFromJmagArea                        =calcCurrentDensity(Irms,2,1,OneSlotAreaInmm2*FillFactor/4);  % Arms/mm2
JrmsFromJmagCoilContour                 =Am2_to_Amm2(18660942.448);
JrmsFromJmagCoilContourModiByFilFactor  =JrmsFromJmagCoilContour/FillFactor;
errorFromCalcJNJContourWithFillFactor   = JrmsFromJmagCoilContourModiByFilFactor-JrmsFromJmagArea  % 0.042
JrmsFromJmagCoilContourModiByFilFactor-JrmsMCAD
OneSlotVolumninM3          =OneSlotArea*mm2m(refDimension.lactive);
DCLossin1SlotNotCorrect    = calcJLoss(JrmsFromJmagCoilContourinAMsqr, OneSlotVolumninM3, rhoJmagDefault)
DCLossin1Slot              = calcJLoss(Amm2_to_Am2(JrmsFromJmagCoilContourModiByFilFactor), OneSlotVolumninM3*FillFactor, rhoJmagDefault)
DCLoss1phFromFilFactor     = DCLossin1Slot*(slots/3)
DCLoss1Ph                  = calcDCLossByJ(JrmsFromJmagCoilContourinAMsqr,OneSlotArea,refDimension.lactive,slots,FillFactor,rhoJmagDefault)

DCLoss1PhByIWaveForm       = rms(DCLossWaveformByIwaveVph)  % 안맞음
DCLoss1PhByIWaveForm       = mean(DCLossWaveformByIwaveVph)  % 안맞음 1.4383e+03
ErrorFromJrmsNIwaveForm    = DCLoss1Ph-DCLoss1PhByIWaveForm  % -51.5715
MeanByDCLossWaveformByI=mean(DCLossWaveformByIwaveVph)*3;    %% mean으로 해도 안맞음 조금큼  4.4695e+03

% By Loss Density
DCLoss1Ph/OneSlotVolumninM3
RMSLossJDnesityContour=122654595.257

(DCLoss1Ph*3)/(RMSLossJDnesityContour*OneSlotVolumninM3)

DCLossByRwEnd=Irms.^2*3*RphwEnd
DCLossByRActive=Irms.^2*3*RphinCircuitActive
MeanByDCLossWaveformByI-DCLossByRActive 
MeanByDCLossWaveformByI-DCLoss1phFromFilFactor*3

Irms.^2*3*RphinCircuitActive-DCLoss1phFromFilFactor*3
%
% 100147057.662*
MQSResultTableFromCSV.ResultTable{1}.R4_{1}.Variables



%% Hybrid

% MQS Plot -DCLossActive
% XTime 
% Z:\01_Codes_Projects\git_fork_emach\mlxperPJT\JEET\deve10_JMAG_MS_ACLoss.m
% line 148


%% GetData N Parsing
%% -Get Data
pole=8


%% MQS
%% Per Layer (No Left & Right)
% init ResultTable N grphObj Cell
filterName={'_Load_','MQS'}
tempCellResultTableFromCSV=readJMAGWholeResultTables(filterName)';
MQSResultTableFromCSV=cell(length(tempCellResultTableFromCSV),3);
MQSResultTableFromCSV=cell2table(MQSResultTableFromCSV);
MQSResultTableFromCSV.Properties.VariableNames={'ResultTable','CSVPath','Name4Mat'};
MQSResultTableFromCSV{:,1}=tempCellResultTableFromCSV;

grphLineObj=cell(height(MQSResultTableFromCSV),1);

% parsing 4plot  Loop Defin
speedList=[1000:2000:13000];
caseIndex=1:length(speedList);
LayerIndexList=[4,3,2,1];
SlotIndexList =[6];
PJTNameList   ={'MQS'}; % !!! add Hybrid MS
ModelNameList ={'SC','ref'}
% Count LoopNumber
NumsingleGraph=length(caseIndex)*len(LayerIndexList)*len(SlotIndexList)*len(PJTNameList)*len(ModelNameList);
NumFigure     = NumsingleGraph/len(speedList)/len(ModelNameList);

startFromZero=0;
lineStyleList={'--','None','None'}
linecolor ={'k','b'};  %'k'= MQS, 'b'=MS
markerList={'+' , 'o' , '*' , '.' , 'x' , 'square' , 'diamond' , 'v' , '^' , '>' , '<' , 'pentagram' , 'hexagram' , ',' , '_' };

%%  Init Variable
% YLimitRange=[-0.4 0.4];
YLabelName ='Joule Loss[W]';
YLimitRange=[-1000 5000];
DCLossPerLayer=DCLossWaveformByIwaveVph/8
%% dev pre MQS Joule Loss

tempJouleLossTable=tempCellResultTableFromCSV{1}.("JouleLoss:W"){caseIndex(1)}
PartNameList      =tempJouleLossTable.Properties.VariableNames';
WirePartName='Wire'
SlotWirePartName  =PartNameList(contains(PartNameList,WirePartName,'IgnoreCase',true));
if ~isempty(SlotWirePartName)
    disp(['도체이름은 "',WirePartName,'"'])
end
grhLinIndex=0;
LineStyle='--'

%%% Plot
% deve10_JMAG_MQS_ACLoss - line 272
% deve10_JMAG_MS_ACLoss - line 161

%% Total Loss 


for CSVIndex=1:length(ProbeCSVPath)
    opts=delimitedTextImportOptions('NumVariables',1000);
    if exist(ProbeCSVPath{CSVIndex},"file")  % CSV File 존재시
    [FileDir,DataNameByCSVName,~]           =fileparts(ProbeCSVPath{CSVIndex});
    parsedMatFilePath=fullfile(FileDir,[DataNameByCSVName,'.mat']);
        if ~exist(parsedMatFilePath,"file") %있으면 불러오지말기
            tempRawTable                            =readtable(ProbeCSVPath{CSVIndex},opts);
            tempRawTable.Properties.Description     =DataNameByCSVName;    
            MQSResultTableFromCSV.CSVPath{CSVIndex}    =ProbeCSVPath{CSVIndex};
            parsedTable                             =parseJMAGResultTable(tempRawTable);
            MQSResultTableFromCSV.ResultTable{CSVIndex}=parsedTable;
            MQSResultTableFromCSV.Name4Mat{CSVIndex}   =DataNameByCSVName;
            save(parsedMatFilePath,"parsedTable")
        else
            MQSResultTableFromCSV.CSVPath{CSVIndex}    =ProbeCSVPath{CSVIndex};
            tempStruct              = load(parsedMatFilePath);
            MQSResultTableFromCSV.ResultTable{CSVIndex}=tempStruct.parsedTable;
            MQSResultTableFromCSV.Name4Mat{CSVIndex}   =DataNameByCSVName;
        end
    end
end
