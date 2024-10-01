% Baseline values for w and h


% Perturbation factor (e.g., 10%)
perturbation = 0.1;


w_base = 3.7;  % 폭 [m]
h_base = 1.6;  % 높이 [m]
% New perturbed values for w and h (increase and decrease by 10%)
w_perturb_up = w_base * (1 + perturbation);
w_perturb_down = w_base * (1 - perturbation);
h_perturb_up = h_base * (1 + perturbation);
h_perturb_down = h_base * (1 - perturbation);

SCFactor=2;

refdimensions=[w_base h_base];
perturbDimWUp           =[w_perturb_up, h_base];
perturbDimHUp           =[w_base, h_perturb_up];
perturbDimWDown         =[w_perturb_down, h_base];
perturbDimHDown         =[w_base, h_perturb_down];

BdisSFTPath='coeffiSCLBdisSFDTableV1.mat'

load(BdisSFTPath)

C = linspecer(1);

for sublindeIndex=1:11
% boxvalue=BrR(1:30,:);
% bx=boxchart(boxvalue','BoxFaceColor','w','BoxEdgeColor','k','Notch','on','BoxMedianLineColor','r');
hold on
figure(1)
BrR=BdisSFDTable.BrRcell{1,1}{sublindeIndex};
     % for idx=1:100
bar(BrR(1:30,:),'grouped','EdgeColor',C,'FaceColor',C)
figure(2)
BrR=BdisSFDTable.BrRcell{1,1}{sublindeIndex};
bar(BrR(1:30,:),'grouped','EdgeColor',C,'FaceColor',C)
figure(2)
BtR=BdisSFDTable.BtRcell{1,1}{sublindeIndex};
bar(BtR(1:30,:),'grouped','EdgeColor',C,'FaceColor',C)
figure(3)
BrL=BdisSFDTable.BrLcell{1,1}{sublindeIndex};
bar(BrL(1:30,:),'grouped','EdgeColor',C,'FaceColor',C)
figure(4)
BtL=BdisSFDTable.BtLcell{1,1}{sublindeIndex};
bar(BtL(1:30,:),'grouped','EdgeColor',C,'FaceColor',C)

     % end
    % title("Single-Sided Amplitude Spectrum of X(t)")
xlabel("Order")
ylabel("|P1(f)|")
end

% BdisSFTPath='D:\KangDH\Emlab_emach\mlxperPJT\JEET\SCLBdisSFDTable.mat'
% BdisSFTPath='D:\KangDH\Emlab_emach\mlxperPJT\BdisSFDTable.mat'
% refTargetTable  =calcSensitivityHYBHarmonicMS(refdimensions*SCFactor)
% TargetTable=calcSensitivityHYBHarmonicMS(refdimensions)
% BdisSFTPath='SCL_TS_16k_BdisSFDTable.mat'
TargetTable=calcHYBHarmonicMS_v1(refdimensions,BdisSFTPath,SCFactor)
% UpWTargetTable  =calcSensitivityHYBHarmonicMS(perturbDimWUp*SCFactor)
% UpHTargetTable  =calcSensitivityHYBHarmonicMS(perturbDimHUp*SCFactor)
% DownWTargetTable=calcSensitivityHYBHarmonicMS(perturbDimWDown*SCFactor)
% DownHTargetTable=calcSensitivityHYBHarmonicMS(perturbDimHDown*SCFactor)
% calcHYBH
% 
% 
% % Sensitivity for w perturbations
% sensitivity_w = ((TotalProx_up_w - TotalProx_orig) / (w_perturb_up - w_base)) * 100;
% sensitivity_w_down = ((TotalProx_down_w - TotalProx_orig) / (w_perturb_down - w_base)) * 100;
% 
% % Sensitivity for h perturbations
% sensitivity_h = ((TotalProx_up_h - TotalProx_orig) / (h_perturb_up - h_base)) * 100;
% sensitivity_h_down = ((TotalProx_down_h - TotalProx_orig) / (h_perturb_down - h_base)) * 100;



%% plot config
ztextShiftRatio= 0.90;

linePlotSlotIndex=[8 2]                                    ;         
eleInterval=100                                        ;         
onePeriodSteps  =240                                   ;             
timeShift       =0                                   ;    
sequenceList    =round([3 40 120 151 220 ]*2/3);
timeList        =round([3 40 120 151 220 ])        ; 
timeNameList   =3/2*timeList-3;
ColorList       =colormap("jet");
timeColorList   =ColorList(1:256/len(timeList):256,:);
timeColorList   = [0 0 0;timeColorList]
timeColorList   =num2cell(timeColorList,2);
timeList        = timeList+timeShift;
lineMarkerList={'-','-','-','-'}
SlotList        ={'square','o','^','v','.','diamond','square','o','^','v','.','diamond','square','o','^','v','.','diamond','square','o','^','v','.','diamond'}
SlotFigIndex    =[2*ones(1,4),3*ones(1,4),4*ones(1,4),5*ones(1,4),6*ones(1,4),7*ones(1,4)]
% close all
N = 6;
X = linspace(0,pi*3,1000);
ColorList = linspecer(N)

ColorList       =num2cell(ColorList,2)
linesize=2

%%
% figure
ProxType='prime'
close all
for speedIdx=1:height(TargetTable)
    af(speedIdx)=figure(speedIdx);
    af(speedIdx).Name=[num2str(TargetTable.speedK(speedIdx)),'krpm'];
    [HYBproxSurf, tempGof, tempSingleDataSet] = createInterpDataSetofStrWithFieldName(TargetTable.dqTable{speedIdx},'TotalHYBProx');
    [surfHYB(speedIdx)]=plotSurf2ndPlane(tempSingleDataSet.xData,HYBproxSurf);
    hold on
    % axHYB=scatter3(tempSingleDataSet.xData,tempSingleDataSet.yData,tempSingleDataSet.zData,'Marker','*','LineWidth',1,'MarkerFaceColor',ColorList{csvindex},'MarkerEdgeColor',ColorList{speedIdx},'DisplayName',[num2str(TargetTable.speedK(speedIdx)),'k[RPM]'])
    if contains(ProxType,'prime')
    surfHYB(speedIdx).FaceAlpha=0.2; 
    surfHYB(speedIdx).LabelColor="k"
    axHYB=surfHYB(speedIdx).Parent;
    % axHYB.Colormap=colormap('parula');
    axLgnd(speedIdx)=legend;
    axLgnd(speedIdx).Location='northwest';
    surfHYB(speedIdx).DisplayName='MS-HYB';
    surfHYB(speedIdx).LineWidth=2;
    setIdqLabel
    end
end
hold on
for speedIdx=1:height(TargetTable)
    figure(speedIdx)
    [TSTotalSurf, tempGof, tempSingleDataSet] = createInterpDataSetofStrWithFieldName(TargetTable.dqTable{speedIdx},'TotalOnlyLoss');
    [surfTS(speedIdx)]=plotSurf2ndPlane(tempSingleDataSet.xData,TSTotalSurf);
    % axTS=scatter3(tempSingleDataSet.xData,tempSingleDataSet.yData,tempSingleDataSet.zData,'Marker','o','SizeData',100,'LineWidth',1,'MarkerFaceColor','None','MarkerEdgeColor',ColorList{speedIdx},'DisplayName',[num2str(TargetTable.speedK(speedIdx)),'k[RPM]'])
    hold on
    % surfTS(speedIdx).EdgeColor="none"; 
    surfTS(speedIdx).FaceAlpha=0.2; 
    surfTS(speedIdx).LineStyle="--";
    % axTS.Colormap=thermal;
    surfTS(speedIdx).LabelColor='flat';
    % axTS=surfTS(speedIdx).Parent;
    axLgnd=legend;
    axLgnd.Location='northwest';
    surfTS(speedIdx).DisplayName='MQS-TS';
    surfTS(speedIdx).LineWidth=2;
    setIdqLabel
end

