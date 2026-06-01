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
cjet=colormap("jet")
colorList=num2cell(cjet(1:20:256,:),2)
MethodList=defHYBProxNameList()
MethodList=MethodList(1:8)
LineList ={'--','-'}
for ModelNStudyIndex=1:2
    for speedIndex=1:len(speedList)
         speed=speedList(speedIndex)
        for MethodIndex=1:len(JMAGHYB_px{ModelNStudyIndex}.TotalACLossPerMethod{1})
        % for MethodIndex=5:len(JMAGHYB_px{ModelNStudyIndex}.TotalACLossPerMethod{1})
            figure(10)
            curMethodWaveForm{speedIndex,MethodIndex}=JMAGHYB_px{ModelNStudyIndex}.TotalACLossPerMethod{speedIndex}{MethodIndex};
            % plot(curMethodWaveForm{speedIndex,MethodIndex}/1000,'color',colorList(speedIndex,:),'Marker',MarkerList{MethodIndex},'DisplayName',MethodList{MethodIndex})
            plot(curMethodWaveForm{speedIndex,MethodIndex}/1000*48,'Color',colorList{MethodIndex},'Marker',markerList{MethodIndex},'DisplayName',[ModelList{ModelNStudyIndex},'',MethodList{MethodIndex},' ',num2str(speed)])
            hold on
        end
    end
    for speedIndex=1:len(speedList)
        for MethodIndex=1:len(JMAGHYB_px{ModelNStudyIndex}.TotalACLossPerMethod{1})
        % for MethodIndex=5:len(JMAGHYB_px{ModelNStudyIndex}.TotalACLossPerMethod{1})
        avgHYBPxList(speedIndex,MethodIndex)=mean(curMethodWaveForm{speedIndex,MethodIndex}/1000*48+4.4)
        end
    end
    for MethodIndex=1:len(JMAGHYB_px{ModelNStudyIndex}.TotalACLossPerMethod{1})
    % for MethodIndex=5:len(JMAGHYB_px{ModelNStudyIndex}.TotalACLossPerMethod{1})
        figure(ModelNStudyIndex)
        plot(speedList(1:len(JMAGHYB_px{ModelNStudyIndex}.TotalACLossPerMethod)),avgHYBPxList(:,MethodIndex)','Color',colorList{MethodIndex},'Marker',markerList{MethodIndex},'LineStyle',LineList{ModelNStudyIndex},'DisplayName',[MethodList{MethodIndex}])
        title(ModelList{ModelNStudyIndex})
        hold on
    end
end