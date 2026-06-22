
figIndex =1;
figure(figIndex)  % same Satu 
for ModelIndex=1:2
    ModelTable=TableList{ModelIndex}
    [~,csvName,~]=fileparts(ModelTable{1,1})
    ModelNameList=strsplit(csvName{1},'_')
    ModelName=ModelNameList{1};
    for SpeedIndex=1:height(REFTable)
        [ACFitResult, tempGof, tempSingleDataSet] = createInterpDataSetofStrWithFieldName(ModelTable.dqTable{SpeedIndex},'TotalACLoss');
        if contains(csvName,'SCL')
          SCLIrms=Kr*tempIsrms;
          Is=sqrt(2)*SCLIrms;
          DCLoss=3*SCLIrms.^2*RdcSCLM;
        else
          Is=sqrt(2)*tempIsrms;
          DCLoss=3*tempIsrms.^2*RdcREF;
        end
        [id,iq]=pkgamma2dq(Is,PhaseAdvance);
        ACperspeed(SpeedIndex)=ACFitResult(id,iq);
    end
    if contains(csvName,'SCL')
        SCLIrms=Kr*tempIsrms;
        DCLossSCL=3*SCLIrms.^2*RdcSCLM/1000;
        SCLTot=ACperspeed;
        SCLAC=ACperspeed-DCLossSCL;
        plot(speedList',ACperspeed,'Marker',markerList{ModelIndex},'lineStyle','--','color',colorList{ModelIndex},'DisplayName',['Act Total: ',ModelName]);
        hold on
        plot(speedList',SCLAC,     'Marker',markerList{ModelIndex},'LineStyle','-','color',colorList{ModelIndex},'DisplayName',['Act AC: ',ModelName])
    else
        DCLossREF    = 3*tempIsrms.^2*RdcREF/1000
        REFTot=ACperspeed;
        REFAC =ACperspeed-DCLossREF;
        plot(speedList',ACperspeed,'Marker',markerList{ModelIndex},'lineStyle','--','color',colorList{ModelIndex},'DisplayName',['Act Total: ',ModelName]);
        hold on

        plot(speedList',REFAC,'Marker',markerList{ModelIndex},'lineStyle','-','color',colorList{ModelIndex},'DisplayName',['Act AC: ',ModelName]);
    end
end
markerObjects = findobj(figure(figIndex), 'Type', 'Axes');
markerObjects.YLabel.String='Loss[kW]'
markerObjects.XLabel.String='Speed[kRPM]'
yyaxis right
TotRatio=plot(speedList',SCLTot./REFTot,'Marker','+','LineStyle','--','Color','r','DisplayName','Act Total SCL/REF')
TotRatio.Parent.YLim=[0, 16];
TotRatio.Parent.YLabel.String='SCL/REF Ratio'
TotRatio.Parent.YColor='r';

aRatio=plot(speedList',SCLAC./REFAC,'Marker','*','LineStyle','-','Color','r','DisplayName','Act AC SCL/REF')
hold on
% clear gcf
legend
setlegendBoxShape(2)
formatterFigure4Paper('double','2x2')
savefig(figure(figIndex),['Comp_SameSatuPerSpeed','gamma',strrep(num2str(PhaseAdvance),'.','_'),'Irms',num2str(tempIsrms)]);

% % Fig3. plot per Speed Same Current
figIndex=2
figure(figIndex)
for ModelIndex=1:2
    ModelTable=TableList{ModelIndex}
    [~,csvName,~]=fileparts(ModelTable{1,1})
    ModelNameList=strsplit(csvName{1},'_')
    ModelName=ModelNameList{1};
    for SpeedIndex=1:height(REFTable)
        [ACFitResult, tempGof, tempSingleDataSet] = createInterpDataSetofStrWithFieldName(ModelTable.dqTable{SpeedIndex},'TotalACLoss');
        if contains(csvName,'SCL')
          SCLIrms=tempIsrms;
          Is=sqrt(2)*SCLIrms;
          DCLoss=3*SCLIrms.^2*RdcSCLM;
        else
          Is=sqrt(2)*tempIsrms;
          DCLoss=3*tempIsrms.^2*RdcREF;
        end
        [id,iq]=pkgamma2dq(Is,PhaseAdvance);
        ACperspeed(SpeedIndex)=ACFitResult(id,iq);
    end 
    if contains(csvName,'SCL')
        SCLIrms=tempIsrms;
        DCLossSCL=3*SCLIrms.^2*RdcSCLM/1000;
        SCLTot=ACperspeed;
        SCLAC=ACperspeed-DCLossSCL;
        plot(speedList',ACperspeed,'Marker',markerList{ModelIndex},'lineStyle','--','color',colorList{ModelIndex},'DisplayName',['Act Total: ',ModelName]);
        hold on
        plot(speedList',SCLAC,     'Marker',markerList{ModelIndex},'LineStyle','-','color',colorList{ModelIndex},'DisplayName',['Act AC: ',ModelName])
    else
        DCLossREF    = 3*tempIsrms.^2*RdcREF/1000
        REFTot=ACperspeed;
        REFAC =ACperspeed-DCLossREF;
        plot(speedList',ACperspeed,'Marker',markerList{ModelIndex},'lineStyle','--','color',colorList{ModelIndex},'DisplayName',['Act Total: ',ModelName]);
        hold on
        plot(speedList',REFAC,'Marker',markerList{ModelIndex},'lineStyle','-','color',colorList{ModelIndex},'DisplayName',['Act AC: ',ModelName]);
    end
end
markerObjects = findobj(figure(figIndex), 'Type', 'Axes');
markerObjects.YLabel.String='Loss[kW]'
markerObjects.XLabel.String='Speed[kRPM]'
yyaxis right
TotRatio=plot(speedList',SCLTot./REFTot,'Marker','+','LineStyle','--','Color','r','DisplayName','Act Total SCL/REF')
TotRatio.Parent.YLim=[0, 16];
TotRatio.Parent.YLabel.String='SCL/REF Ratio'
TotRatio.Parent.YColor='r';

aRatio=plot(speedList',SCLAC./REFAC,'Marker','*','LineStyle','-','Color','r','DisplayName','Act AC SCL/REF')
hold on
grid on
legend
setlegendBoxShape(2)
formatterFigure4Paper('double','2x2')
savefig(figure(figIndex),['Comp_SameIpkPerSpeed','gamma',strrep(num2str(PhaseAdvance),'.','_'),'Irms',num2str(tempIsrms)]);
