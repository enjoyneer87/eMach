% D:\KangDH\Emlab_emach\mlxperPJT\JEET\devSurfInterp4HYB.m 
clear
load('WireFitTables_SCL_TS_18krpm_case28.mat')

%% def Names
WireTabNames=WireFitTable.Name;
SlotNumberCell=extractBetween(WireTabNames,'Slot','/Wire');
SlotNumberList=unique(SlotNumberCell);
WireNumberCell=extractAfter(WireTabNames,'/Wire');
WireNumberList=unique(WireNumberCell);
%% FFT
for slotIndex=1:height(WireFitTable)
    LayerNumber=WireNumberCell{slotIndex};
    SlotNumber= SlotNumberCell{slotIndex};
    figure('Name',['slot',SlotNumber,'Layer',LayerNumber])
    NumsubLine=len(WireFitTable.RightX{slotIndex});
    for sublineIndex=1:NumsubLine
    subplot(4,1,1)
    hold on
    [BrR,~,bxrr]=getFFT1Dset([WireFitTable.Br3DRightArray{slotIndex}{sublineIndex}]');   
    subplot(4,1,2)
    hold on
    [BtR,~,bxtr]=getFFT1Dset([WireFitTable.Bt3DRightArray{slotIndex}{sublineIndex}]');   
    subplot(4,1,3)
    hold on
    [Brl,~,bxrl]=getFFT1Dset([WireFitTable.Br3DLeftArray{slotIndex}{sublineIndex}]');   
    subplot(4,1,4)
     hold on
    [Btl,~,bxtl]=getFFT1Dset([WireFitTable.Bt3DLeftArray{slotIndex}{sublineIndex}]');   
    end
end


BSFDrrPerSLot=cell(height(WireFitTable),1);
BSFDtrPerSLot=cell(height(WireFitTable),1);
BSFDrlPerSLot=cell(height(WireFitTable),1);
BSFDtlPerSLot=cell(height(WireFitTable),1);

for slotIndex=1:height(WireFitTable)
    BSfDrr=cell(NumsubLine,1);
    BSfDtr=cell(NumsubLine,1);
    BSfDrl=cell(NumsubLine,1);
    BSfDtl=cell(NumsubLine,1);
   NumsubLine=len(WireFitTable.RightX{slotIndex});

    for sublineIndex=1:NumsubLine
     BSfDrr{sublineIndex}=(WireFitTable.Br3DRightArray{slotIndex}{sublineIndex}).^2;
     BSfDtr{sublineIndex}=(WireFitTable.Bt3DRightArray{slotIndex}{sublineIndex}).^2;
     BSfDrl{sublineIndex}=(WireFitTable.Br3DLeftArray{slotIndex}{sublineIndex}).^2;
     BSfDtl{sublineIndex}=(WireFitTable.Bt3DLeftArray{slotIndex}{sublineIndex}).^2;
    end
    BSFDrrPerSLot{slotIndex}=BSfDrr;
    BSFDtrPerSLot{slotIndex}=BSfDtr;
    BSFDrlPerSLot{slotIndex}=BSfDrl;
    BSFDtlPerSLot{slotIndex}=BSfDtl;
end
WireFitTable.BSFDrrPerSLot=BSFDrrPerSLot;
WireFitTable.BSFDtrPerSLot=BSFDtrPerSLot;
WireFitTable.BSFDrlPerSLot=BSFDrlPerSLot;
WireFitTable.BSFDtlPerSLot=BSFDtlPerSLot;

%% BSF Plot
BrR=cell(height(WireFitTable),4);
BtR=cell(height(WireFitTable),4);
BrL=cell(height(WireFitTable),4);
BtL=cell(height(WireFitTable),4);

for slotIndex=1:height(WireFitTable)
   LayerNumber=WireNumberCell{slotIndex};
   SlotNumber= SlotNumberCell{slotIndex};
   figure('Name',['slot',SlotNumber,'Layer',LayerNumber])
   NumsubLine=len(WireFitTable.RightX{slotIndex});
      for sublineIndex=1:NumsubLine
       subplot(2,2,1)
        hold on
            [BrL{slotIndex,sublineIndex},~,~]=getFFT1Dset(WireFitTable.BSFDrlPerSLot{slotIndex}{sublineIndex});
        subplot(2,2,2)
        hold on
        [BrR{slotIndex,sublineIndex},~,~]=getFFT1Dset([WireFitTable.BSFDrrPerSLot{slotIndex}{sublineIndex}]);   
        subplot(2,2,3)
        hold on
            [BtL{slotIndex,sublineIndex},~,~]=getFFT1Dset(WireFitTable.BSFDtlPerSLot{slotIndex}{sublineIndex});
        subplot(2,2,4)
        hold on
            [BtR{slotIndex,sublineIndex},~,~]=getFFT1Dset(WireFitTable.BSFDtrPerSLot{slotIndex}{sublineIndex});   
      end
end
%% BSF * freqE Plot
WireLayerInterGap=WireFitTable.subLineRPos{2}(2)-WireFitTable.subLineRPos{2}(1);
BrDataSize=size(WireFitTable.Bt3DLeftArray{1}{:})
WireWidth_division=BrDataSize(2);
TimeSteps=BrDataSize(1);
refdimensions=[3.7 1.8]*2;
simulRPM= 18000
stackLenmm=150
lactive=mm2m(stackLenmm);
pp=  4;
for slotIndex=1:height(WireFitTable)
       LayerNumber=WireNumberCell{slotIndex};
      SlotNumber= SlotNumberCell{slotIndex};
       NumsubLine=len(WireFitTable.RightX{slotIndex});
      for sublineIndex=1:NumsubLine
        orderList=[1:TimeSteps/2+1];
        freqE=rpm2freqE(simulRPM,pp);
        freqListRow=freqE*orderList;
        if sublineIndex==NumsubLine
            heff=refdimensions(2);     
        else
            heff=WireLayerInterGap;
        end
        dimensions= [refdimensions(1)/WireWidth_division heff];
        [coeffiRadial,coeffiTheta]=calcProx2DG2(dimensions,freqListRow);
        Prlcom{slotIndex}=BrL{slotIndex,sublineIndex}'.*coeffiRadial;
        Prrcom{slotIndex}=BrR{slotIndex,sublineIndex}'.*coeffiRadial;
        Ptlcom{slotIndex}=BtL{slotIndex,sublineIndex}'.*coeffiTheta;
        Ptrcom{slotIndex}=BtR{slotIndex,sublineIndex}'.*coeffiTheta;
      end
end
3.7*2/100
 % mean(sum(Prrcom,2))
%% harmonic Loss 
% close all
for slotIndex=1:height(WireFitTable)
figure(1)
hold on
plot(sum(Prrcom{slotIndex},2)/1000,'LineWidth',2,'LineStyle','--')
plot(sum(Prlcom{slotIndex},2)/1000)
figure(2)
hold on
plot(sum(Ptrcom{slotIndex},2)/1000,'LineWidth',2,'LineStyle','--')
plot(sum(Ptlcom{slotIndex},2)/1000)
end


%%
for slotIndex=1:height(WireFitTable)
figure(1)
hold on
scatter(slotIndex,sum(sum(Prrcom{slotIndex},2))/1000)
scatter(slotIndex,sum(sum(Prlcom{slotIndex},2))/1000)
figure(2)
hold on
scatter(slotIndex,sum(sum(Ptrcom{slotIndex},2))/1000)
scatter(slotIndex,sum(sum(Ptlcom{slotIndex},2))/1000)
end

%% Total Loss
totalGoReturnProx=0;
for slotIndex=1:height(WireFitTable)
totalGoReturnProx= totalGoReturnProx+(sum(sum(Prrcom{slotIndex},2))/1000+sum(sum(Prrcom{slotIndex},2))/1000+...
sum(sum(Ptrcom{slotIndex},2))/1000+sum(sum(Ptlcom{slotIndex},2))/1000);
end

TotalProxPhase=totalGoReturnProx/2;
TotalProxPhase*3*lactive*16;


%% FreqE Coeffi
plot(freqListRow/1000,coeffiRadial,'DisplayName','radial')
hold on
plot(freqListRow/1000,coeffiTheta,'DisplayName','tangential')
ax=gca
ax.XLabel.String='Frequency[kHz]'
ax.YLabel.String='Coefficient'
%% Box
boxplot
bar(BSFD(1:30,:),'grouped')
(coeffiRadial.*Brmag.^2+coeffiTheta.*Btmag.^2)
P_total, P_frequencies] = calcHarmonicHybridACLoss(conductorType, refdimensions, sigma, mu_c, frequencies, B_r_array, B_theta_m_array, l)
calcHybridACLossWave



%%Backup 

load('SCl_case28_MS_B_RTTable')
load('SCl_case28_TS_B_RTTable')

for slotIndex=1:4
clear SlottempB
SlottempB=TSFieldRTTable{1}(slotIndex,:);
tempCellArray=cellfun(@(x) x.^2,SlottempB,'UniformOutput',false)
MS_SFDR{slotIndex}=tempCellArray(1,241:480)

clear SlottempB
SlottempB=TSFieldRTTable{2}(slotIndex,:);
tempCellArray=cellfun(@(x) x.^2,SlottempB,'UniformOutput',false)
MS_SFDT{slotIndex}=tempCellArray(1,241:480)

end



for slotIndex=1:4
clear SlottempB
SlottempB=MSFieldRTTable{1}(slotIndex,:);
TS_SFDR{slotIndex}=cellfun(@(x) x.^2,SlottempB,'UniformOutput',false)
clear SlottempB
SlottempB=MSFieldRTTable{2}(slotIndex,:);
TS_SFDT{slotIndex}=cellfun(@(x) x.^2,SlottempB,'UniformOutput',false)
end



a=MS_SFDT{slotIndex}

TS_SFDR{1}{}

for slotIndex=1:1
dif_SFDT=cellfun(@(x,y) x-y,TS_SFDT{slotIndex},MS_SFDT{slotIndex},'UniformOutput',false)
end