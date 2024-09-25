function [TotalACLossPerMethod,DisplaynameList]=devcalcAllHybridACFromBtable(speed,pole,refDim,RTargetTable,thetaTargetTable)
%% dev
% RTargetTable  =MSRTargetTable{ModelNStudyIndex}(1,:)
% thetaTargetTable=MSthetaTargetTable{ModelNStudyIndex}(1,:)

DisplaynameList           =defHYBProxNameList();
DisplaynameList           =DisplaynameList(1:7);

PosLayName             =RTargetTable.Properties.VariableNames;
PosLayName           =cellfun(@(x) strrep(x,'_(R)',''),PosLayName,'UniformOutput',false);
DisplaynameList           =cellfun(@(x) strrep(x,'_',' '),DisplaynameList,'UniformOutput',false);

aclossPerLayer           =cell(width(PosLayName),length(DisplaynameList));
% gr=cell(1,width(DisplaynameList));
%% calc Per Layer B
for LayerIndex=1:width(PosLayName)
    Bfield.Br                 =RTargetTable{1,LayerIndex}{:}(end-120:end,:).Variables;
    Bfield.Bthetam            =thetaTargetTable{1,LayerIndex}{:}(end-120:end,:).Variables;
    %% calc Function
   [P1DG1P,P1DG2P,P2DG1P,P2DG2P,P2DG1,P2DG2,PrectP]  = calcHybridACLossWave('rectangular', refDim, rpm2freqE(speed,pole/2),Bfield);
    %% Freq2 Time 
    freq2TimeFactor=2;
    aclossPerLayer{LayerIndex,1}=P1DG1P*freq2TimeFactor                            ;  
    aclossPerLayer{LayerIndex,2}=P1DG2P                           ; 
    aclossPerLayer{LayerIndex,3}=P2DG1P*freq2TimeFactor                            ;  
    aclossPerLayer{LayerIndex,4}=P2DG2P                           ; 
    aclossPerLayer{LayerIndex,5}=P2DG1*freq2TimeFactor           ;
    aclossPerLayer{LayerIndex,6}=P2DG2                           ;     
    aclossPerLayer{LayerIndex,7}=PrectP*freq2TimeFactor           ;  
end
    % totalACgrph                      =cell(1,width(aclossPerLayer));
    TotalACLossPerMethod           =cell(width(aclossPerLayer),1);
%% To TotalACPerMethod Cell    
for MethodIndex =1:width(aclossPerLayer)
    TotalACLossPerMethod{MethodIndex,1}=zeros(121,1);
    for LayerIndex=1:width(RTargetTable)
        if ~isempty(aclossPerLayer{LayerIndex,MethodIndex})
           TotalACLossPerMethod{MethodIndex,1}     =TotalACLossPerMethod{MethodIndex,1}+aclossPerLayer{LayerIndex,MethodIndex};
        end
    end
end
     % figure(MethodIndex)
     % totalACgrph{MethodIndex}=plotTransientTable(TotalACLossPerMethod{MethodIndex,1});
     % totalACgrph{MethodIndex}{1}.DisplayName=['Total',DisplaynameList{MethodIndex},'@',num2str(speed)];
     % hold on
end
% totalJouleGrph=cell(1,width(aclossPerLayer));
% %% Including DC
% for NewIndex=1:width(aclossPerLayer)
%     figure(NewIndex)
%     Pavg{NewIndex}=mean(TotalDCAC{NewIndex,1});
%     meanLineMS{NewIndex}=yline(Pavg{NewIndex});
%     meanLineMS{NewIndex}.DisplayName=['Mean','DC+AC Slot6 ','@',num2str(speed)];
%     meanLineMS{NewIndex}.LineWidth=2;
%     meanLineMS{NewIndex}.LineStyle='-';
%     meanLineMS{NewIndex}.Color=[0 114 189]/256;
%     hold on
%     textObj(NewIndex).FontSize=12;
%     textObj(NewIndex).Color=[0 114 189]/256;
%     % % totalJouleGrph{NewIndex}=plotTransientTable(TotalDCAC{NewIndex,1});
%     % totalJouleGrph{NewIndex}{1}.DisplayName=['DC+AC Slot6 ',DisplaynameList{NewIndex},'@',num2str(speed)];
%     % totalJouleGrph{NewIndex}{1}.LineWidth=2;
%     % totalJouleGrph{NewIndex}{1}.LineStyle='-';
%     % totalJouleGrph{NewIndex}{1}.Marker     ='^';
%     % totalJouleGrph{NewIndex}{1}.Color     = [0 114 189]/256;
%     % totalJouleGrph{NewIndex}{1}.MarkerFaceColor     = [0 114 189]/256;
%     formatterFigure4Paper('Double','2x2');
%     ax=convertFigXAxisToElecDeg(0);
% end
