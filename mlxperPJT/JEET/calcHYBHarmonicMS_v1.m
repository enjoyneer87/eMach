% D:\KangDH\Emlab_emach\mlxperPJT\JEET\devSurfInterp4HYBMSv1.m
    % D:\KangDH\Emlab_emach\mlxperPJT\JEET\devmkBSFDTable.m
% mergeFigures([1 2])
function TargetTable=calcHYBHarmonicMS_v1(refdimensions,BdisSFTPath,SCFactor)
% close all
% properties
% BSFDTable
% WireFitTable
% TargetTable
%% to be Out of Function
    refdimensions=refdimensions*SCFactor;
     %% load TS Data 2 compare
    % D:\KangDH\Emlab_emach\mlxperPJT\JEET\devmkDqTableformat.m
    load('SCLTableMapPerSpeed.mat');
    load('REFTableMapPerSpeed.mat');
    CSVList=[REFTable;SCLTable];
    CSVList=table2cell(CSVList);
    % close all
    Kr=SCFactor;
    load('Rdcactive.mat')
    RdcSCL=RdcREF./Kr.^2;
    RdcSCLM=RdcSCL;
    for csvindex=1:height(REFTable)
        REFTable.dqTable{csvindex}.TotalDCLoss   =3*(REFTable.dqTable{csvindex}.Is./sqrt(2)).^2*RdcREF/1000;
        REFTable.dqTable{csvindex}.TotalOnlyLoss =REFTable.dqTable{csvindex}.TotalACLoss -REFTable.dqTable{csvindex}.TotalDCLoss;
    end
    
    for csvindex=1:height(SCLTable)
        SCLTable.dqTable{csvindex}.TotalDCLoss   =3*(SCLTable.dqTable{csvindex}.Is./sqrt(2)).^2*RdcSCL/1000;
        SCLTable.dqTable{csvindex}.TotalOnlyLoss =SCLTable.dqTable{csvindex}.TotalACLoss -SCLTable.dqTable{csvindex}.TotalDCLoss;
    end
    %% Scaling 
    if SCFactor>1
        TargetTable=SCLTable;
    else
        TargetTable=REFTable;
    end


%% get BSFDTable. ref mk BSFDTable
    % D:\KangDH\Emlab_emach\mlxperPJT\JEET\devmkBSFDTable.m
    % figIndex=2;
    ProxType='prime';
    % SCFactor=2;
    if nargin>2
    load(BdisSFTPath)
    else
    load('D:\KangDH\Emlab_emach\mlxperPJT\JEET\coeffiSCLBdisSFDTable.mat');
    end
    %% Get MatFile Path of BSFD Table
    MatfileNames=BdisSFDTable.MatFileName;
    %% def Aux Data
    load(MatfileNames{1});
    WireTabNames=WireFitTable.Name;
    SlotNumberCell=extractBetween(WireTabNames,'Slot','/Wire');
    SlotNumberList=unique(SlotNumberCell);
    NumCalcTargetSlots=len(SlotNumberList);
    WireLayerInterGap=WireFitTable.subLineRPos{2}(2)-WireFitTable.subLineRPos{2}(1);
    if contains(WireTabNames,'SC')&SCFactor==1
        WireLayerInterGap=WireLayerInterGap/2;
    end
    %% delete C.p Target

    %% temp Dim
    stackLenmm=150;
    lactive=mm2m(stackLenmm);
    pp=  4;
    NumSlots=48;
    NumslotWire=height(BdisSFDTable.BrRcell{1});
    %% Speed Dependency
    for speedIdx=1:height(TargetTable)    % change simulRPM as fcn input (Type : array)
        simulRPM= TargetTable.speedK(speedIdx)*1000;
        for caseIndex=1:height(BdisSFDTable)       % case 
            % size def                      
             PrlcomPerCase=cell(NumslotWire,1);
             PrrcomPerCase=cell(NumslotWire,1);
             PtlcomPerCase=cell(NumslotWire,1);
             PtrcomPerCase=cell(NumslotWire,1);
             totalGoReturnProx=0;
            for slotWireIDX=1:NumslotWire  % slot Wire
              %% size def
              NumsubLine=len(removeEmptyCells([BdisSFDTable.BrRcell{caseIndex}(slotWireIDX,:)]));
              for sublineIndex=1:NumsubLine
                    %% size def
                    BrDataSize=size(BdisSFDTable.BrRcell{caseIndex}{slotWireIDX,sublineIndex});
                    FFTorderList          =1:BrDataSize(1);
                    NumWidthDivPerConductor =BrDataSize(2);
                    freqE=rpm2freqE(simulRPM,pp);
                    freqListRow=freqE*FFTorderList;
                    dimensions= [refdimensions(1)/NumWidthDivPerConductor WireLayerInterGap];
                    if contains(ProxType,'non')
                    [coeffiRadial,coeffiTheta]=calcProx2DG2(dimensions,freqListRow);
                    elseif contains(ProxType,'prime')
                    [coeffiRadial,coeffiTheta]=calcProx2DG2Prime(dimensions,freqListRow);
                    end
                    PrlcomPerCase{slotWireIDX,1}=BdisSFDTable.BrLcell{caseIndex}{slotWireIDX,sublineIndex}'.*coeffiRadial;
                    PrrcomPerCase{slotWireIDX,1}=BdisSFDTable.BrRcell{caseIndex}{slotWireIDX,sublineIndex}'.*coeffiRadial;
                    PtlcomPerCase{slotWireIDX,1}=BdisSFDTable.BtLcell{caseIndex}{slotWireIDX,sublineIndex}'.*coeffiTheta;
                    PtrcomPerCase{slotWireIDX,1}=BdisSFDTable.BtRcell{caseIndex}{slotWireIDX,sublineIndex}'.*coeffiTheta;
                    totalGoReturnProx= ...
                    totalGoReturnProx+...
                    sum(sum(PrlcomPerCase{slotWireIDX},2))/1000+sum(sum(PtlcomPerCase{slotWireIDX},2))/1000+...
                    sum(sum(PrrcomPerCase{slotWireIDX},2))/1000+sum(sum(PtrcomPerCase{slotWireIDX},2))/1000;
              end
            end
            %% Sum each Harmonic & Spatial 
            TotalProxPhase=totalGoReturnProx/(NumCalcTargetSlots/2);
            % TotalProx=TotalProxPhase*lactive*NumSlots*2;

            TotalProx=TotalProxPhase*lactive*NumSlots*((2*2/ sqrt(speedIdx)) * (SCFactor - 1) + 2*(2 - SCFactor));
            BdisSFDTable.TotalProx{caseIndex}=TotalProx;   
        end
        TargetTable.dqTable{speedIdx}.TotalHYBProx=cell2mat(BdisSFDTable.TotalProx);
    end
end


