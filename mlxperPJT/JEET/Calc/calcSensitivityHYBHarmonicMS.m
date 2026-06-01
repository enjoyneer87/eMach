% D:\KangDH\Emlab_emach\mlxperPJT\JEET\devSurfInterp4HYBMS.m
    % D:\KangDH\Emlab_emach\mlxperPJT\JEET\devmkBSFDTable.m
% mergeFigures([1 2])
function TargetTable=calcSensitivityHYBHarmonicMS(refdimensions,BdisSFTPath,SCFactor)
% close all
% properties
% BSFDTable
% WireFitTable
% TargetTable
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
              %% BSFD * order freqE 
             PrlcomPerCase=cell(NumslotWire,1);
             PrrcomPerCase=cell(NumslotWire,1);
             PtlcomPerCase=cell(NumslotWire,1);
             PtrcomPerCase=cell(NumslotWire,1);
            for slotWireIDX=1:NumslotWire  % slot Wire
                %% size def
              NumsubLine=len(removeEmptyCells([BdisSFDTable.BrRcell{caseIndex}(slotWireIDX,:)]));
              for sublineIndex=1:NumsubLine
                    BrDataSize=size(BdisSFDTable.BrRcell{caseIndex}{slotWireIDX,sublineIndex});
                    
                    FFTorderList          =1:BrDataSize(1);
                    NumWidthDivPerConductor =BrDataSize(2);
                    freqE=rpm2freqE(simulRPM,pp);
                    freqListRow=freqE*FFTorderList;
                    % if sublineIndex==NumsubLine
                    %     heff=refdimensions(2);     
                    % else
                    %     heff=WireLayerInterGap;
                    % end
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
              end
            end
            %% Sum each Harmonic & Spatial 
            totalGoReturnProx=0;
            for slotWireIDX=1:NumslotWire
                totalGoReturnProx= ...
                totalGoReturnProx+...
                 sum(sum(PrlcomPerCase{slotWireIDX},2))/1000+sum(sum(PtlcomPerCase{slotWireIDX},2))/1000+...
                 sum(sum(PrrcomPerCase{slotWireIDX},2))/1000+sum(sum(PtrcomPerCase{slotWireIDX},2))/1000;
            end
            TotalProxPhase=totalGoReturnProx/(NumCalcTargetSlots/2);
            TotalProx=TotalProxPhase*lactive*NumSlots;
            BdisSFDTable.TotalProx{caseIndex}=TotalProx;   
        end
        TargetTable.dqTable{speedIdx}.TotalHYBProx=cell2mat(BdisSFDTable.TotalProx);
    end

    %%
    % figure
    for speedIdx=1:4
        [HYBproxSurf, tempGof, tempSingleDataSet] = createInterpDataSetofStrWithFieldName(TargetTable.dqTable{speedIdx},'TotalHYBProx');
        axHYB=plotSurf2ndPlane(tempSingleDataSet.xData,HYBproxSurf);
        hold on
        if contains(ProxType,'prime')
        axHYB.FaceAlpha=0.8/speedIdx; 
        axHYB.EdgeColor="interp";
        end
        [TSTotalSurf, tempGof, tempSingleDataSet] = createInterpDataSetofStrWithFieldName(TargetTable.dqTable{speedIdx},'TotalOnlyLoss');
        axTS=plotSurf2ndPlane(tempSingleDataSet.xData,TSTotalSurf);
        axDq=axTS.Parent;
        hold on
        axTS.EdgeColor="none"; 
    end
    
end
% mean(sum(Prrcom,2))
% %% harmonic Loss 
% % close all
% for slotIndex=1:height(WireFitTable)
% figure(1)
% hold on
% plot(sum(Prrcom{slotIndex},2)/1000,'LineWidth',2,'LineStyle','--')
% plot(sum(Prlcom{slotIndex},2)/1000)
% figure(2)
% hold on
% plot(sum(Ptrcom{slotIndex},2)/1000,'LineWidth',2,'LineStyle','--')
% plot(sum(Ptlcom{slotIndex},2)/1000)
% end
% 
% 
% %%
% for slotIndex=1:height(WireFitTable)
% figure(1)
% hold on
% scatter(slotIndex,sum(sum(Prrcom{slotIndex},2))/1000)
% scatter(slotIndex,sum(sum(Prlcom{slotIndex},2))/1000)
% figure(2)
% hold on
% scatter(slotIndex,sum(sum(Ptrcom{slotIndex},2))/1000)
% scatter(slotIndex,sum(sum(Ptlcom{slotIndex},2))/1000)
% end



