% D:\KangDH\Emlab_emach\mlxperPJT\JEET\devSurfInterp4HYBMS.m
    % D:\KangDH\Emlab_emach\mlxperPJT\JEET\devmkBSFDTable.m
% mergeFigures([1 2])
clear
% close all
figIndex=2
ProxType='prime'
SCFactor=2;
load('BdisSFDTable.mat');

% get Dta
matFileList=findMatFiles(pwd)';
matFileList=matFileList(contains(matFileList,'wire'));
MSmatFileList=matFileList(contains(matFileList,'MS'));
REFmatFileList=MSmatFileList(contains(MSmatFileList,'SCL'));
REFmatFileList=REFmatFileList(contains(REFmatFileList,'MagB'));
REFDTmatFileList=REFmatFileList(contains(REFmatFileList,'DT'));
[~,MatfileNames,~]=fileparts(REFDTmatFileList);

%% def
load(MatfileNames{1})
WireLayerInterGap=WireFitTable.subLineRPos{2}(2)-WireFitTable.subLineRPos{2}(1);
BrDataSize       =size(WireFitTable.Bt3DLeftArray{1}{:});
WireWidth_division=BrDataSize(2);
TimeSteps=BrDataSize(1);
refdimensions=[3.7 1.6]*SCFactor;

load(MatfileNames{1,1})
%% def Names
WireTabNames=WireFitTable.Name;
SlotNumberCell=extractBetween(WireTabNames,'Slot','/Wire');
SlotNumberList=unique(SlotNumberCell);
NumCalcTargetSlots=len(SlotNumberList);
%% mk BSFD Table
% D:\KangDH\Emlab_emach\mlxperPJT\JEET\devmkBSFDTable.m
%% load TS Data 2 compare
% D:\KangDH\Emlab_emach\mlxperPJT\JEET\devmkDqTableformat.m
load('SCLTableMapPerSpeed.mat');
load('REFTableMapPerSpeed.mat');
CSVList=[REFTable;SCLTable]
CSVList=table2cell(CSVList)
% close all
Kr=2;
load('Rdcactive.mat')
RdcSCL=RdcREF./Kr.^2
RdcSCLM=RdcSCL;
for csvindex=1:height(REFTable)
    REFTable.dqTable{csvindex}.TotalDCLoss   =3*(REFTable.dqTable{csvindex}.Is./sqrt(2)).^2*RdcREF/1000;
    REFTable.dqTable{csvindex}.TotalOnlyLoss =REFTable.dqTable{csvindex}.TotalACLoss -REFTable.dqTable{csvindex}.TotalDCLoss;
end

for csvindex=1:height(SCLTable)
    SCLTable.dqTable{csvindex}.TotalDCLoss   =3*(SCLTable.dqTable{csvindex}.Is./sqrt(2)).^2*RdcSCL/1000;
    SCLTable.dqTable{csvindex}.TotalOnlyLoss =SCLTable.dqTable{csvindex}.TotalACLoss -SCLTable.dqTable{csvindex}.TotalDCLoss;
end
%%
if SCFactor>1
    TargetTable=SCLTable;
else
    TargetTable=REFTable;
end

stackLenmm=150;
lactive=mm2m(stackLenmm);
pp=  4;
NumSlots=48;
NumslotWire=height(BdisSFDTable.BrRcell{1});
%% Speed Dependency
for speedIdx=1:height(TargetTable)
    simulRPM= TargetTable.speedK(speedIdx)*1000;
  
    for caseIndex=1:height(BdisSFDTable)       % case 
          %% BSFD * order freqE 
         PrlcomPerCase=cell(NumslotWire,1);
         PrrcomPerCase=cell(NumslotWire,1);
         PtlcomPerCase=cell(NumslotWire,1);
         PtrcomPerCase=cell(NumslotWire,1);
        for slotWireIDX=1:NumslotWire  % slot Wire
          NumsubLine=len(removeEmptyCells([BdisSFDTable.BrRcell{caseIndex}(slotWireIDX,:)]));
          for sublineIndex=1:NumsubLine
                orderList=1:TimeSteps/2+1;
                freqE=rpm2freqE(simulRPM,pp);
                freqListRow=freqE*orderList;
                if sublineIndex==NumsubLine
                    heff=refdimensions(2);     
                else
                    heff=WireLayerInterGap;
                end
                dimensions= [refdimensions(1)/WireWidth_division heff];
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
% figure(figIndex)
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
hold on
axTS.EdgeColor="none";

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



