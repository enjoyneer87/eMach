% function [TotalACLossPerMethod,TotalDCAC,DisplaynameList,Pavg]=calcAllHybridACFromBtable(speed,pole,refDim,RTargetTable,thetaTargetTable,DCLossWaveformByIwaveVph)
%% dev
% RTargetTable  =MSRTargetTable{ModelNStudyIndex}(1,:)
% thetaTargetTable=MSthetaTargetTable{ModelNStudyIndex}(1,:)
% RTargetTable=MSRTargetTable{ModelNStudyIndex}{1,1}

DisplaynameList={'P_rect'...      % ,'P_Instant 1D'      ...      
,'P_rect 1D G1'       ... % ,'P rect 1D G2'        ...% ,'P_rect nonGamma'... % ,'P_rect MCAD 1D'    ...
,'P_rect 2D G1'};       
% ,'P_rect 2D G2'};        

PosLayName=RTargetTable.Properties.VariableNames
PosLayName=cellfun(@(x) strrep(x,'_(R)',''),PosLayName,'UniformOutput',false)
DisplaynameList=cellfun(@(x) strrep(x,'_',' '),DisplaynameList,'UniformOutput',false)

aclossPerLayer=cell(width(PosLayName),length(DisplaynameList));
% gr=cell(1,width(DisplaynameList));
for LayerIndex=1:width(PosLayName)
    Bfield4LayerLeft.Br                 =RTargetTable{1,LayerIndex}{:}(end-120:end,:).Variables;
    Bfield4LayerLeft.Bthetam            =thetaTargetTable{1,LayerIndex}{:}(end-120:end,:).Variables;
    [P_rect,...
     P_1DInstant,...
     P_1DrectG1,...
     P1DrectG2,...
     P_rect_nonGamma,...
     P_rectMCAD1D,...
     P_rec2DG1,...
     P_rec2DG2]                         = calcHybridACLossWave('rectangular', refDim, rpm2freqE(speed,pole/2),Bfield4LayerLeft);
    
    aclossPerLayer{LayerIndex,1}=1000*P_rect               ;     
    % aclossPerLayer{LayerIndex,2}=1000*P_1DInstant          ;         
    aclossPerLayer{LayerIndex,2}=1000*P_1DrectG1           ;         
    % aclossPerLayer{LayerIndex,3}=1000*P1DrectG2            ;     
    % aclossPerLayer{LayerIndex,5}=1000*P_rect_nonGamma      ;             
    % aclossPerLayer{LayerIndex,6}=P_rectMCAD1D         ;         
    aclossPerLayer{LayerIndex,3}=1000*P_rec2DG1            ;     
    % aclossPerLayer{LayerIndex,8}=1000*P_rec2DG2            ;         
    
    % TotalArrayOfEachPositionNLayer=1000.*[P_rect,...
    %                                     P_1DInstant,...
    %                                     P_1DrectG1,...
    %                                     P1DrectG2,...
    %                                     P_rect_nonGamma,...
    %                                     P_rectMCAD1D,...
    %                                     P_rec2DG1,...
    %                                     P_rec2DG2];
    % for MethodIndex=1:width(aclossPerLayer)
    %     figure(MethodIndex)
    %     if ~isempty(aclossPerLayer{LayerIndex,MethodIndex})
    %     gr{MethodIndex}=plotTransientTable(aclossPerLayer{LayerIndex,MethodIndex});
    %     gr{MethodIndex}{1}.DisplayName=[DisplaynameList{MethodIndex},PosLayName{LayerIndex}];
    %     end
    %     hold on
    % end
end

    totalACgrph         =cell(1,width(aclossPerLayer));
    TotalACLossPerMethod=cell(width(aclossPerLayer),1);

for MethodIndex=1:width(aclossPerLayer)
    TotalACLossPerMethod{MethodIndex,1}=zeros(121,1);
    for LayerIndex=1:width(RTargetTable)
        if ~isempty(aclossPerLayer{LayerIndex,MethodIndex})
           TotalACLossPerMethod{MethodIndex,1}=TotalACLossPerMethod{MethodIndex,1}+aclossPerLayer{LayerIndex,MethodIndex};
        end
    end
     % figure(MethodIndex)
     % totalACgrph{MethodIndex}=plotTransientTable(TotalACLossPerMethod{MethodIndex,1});
     % totalACgrph{MethodIndex}{1}.DisplayName=['Total',DisplaynameList{MethodIndex},'@',num2str(speed)];
     % hold on
end

TotalDCAC     =cell(width(aclossPerLayer),1);
totalJouleGrph=cell(1,width(aclossPerLayer));
%% Including DC
for NewIndex=1:width(aclossPerLayer)
    figure(NewIndex)
    TotalDCAC{NewIndex,1}=TotalACLossPerMethod{NewIndex,1}+DCLossWaveformByIwaveVph;
    Pavg{NewIndex}=mean(TotalDCAC{NewIndex,1});
    meanLineMS{NewIndex}=yline(Pavg{NewIndex});
    meanLineMS{NewIndex}.DisplayName=['Mean','DC+AC Slot6 ','@',num2str(speed)];
    meanLineMS{NewIndex}.LineWidth=2;
    meanLineMS{NewIndex}.LineStyle='-';
    meanLineMS{NewIndex}.Color=[0 114 189]/256;
    hold on
    textObj(NewIndex)=text(180,mean(TotalDCAC{NewIndex,1})*1.05,[num2str(mean(TotalDCAC{NewIndex,1}),'%.2f'),'@',num2str(speed)]);
    textObj(NewIndex).FontSize=12;
    textObj(NewIndex).Color=[0 114 189]/256;
    totalJouleGrph{NewIndex}=plotTransientTable(TotalDCAC{NewIndex,1});
    totalJouleGrph{NewIndex}{1}.DisplayName=['DC+AC Slot6 ',DisplaynameList{NewIndex},'@',num2str(speed)];
    totalJouleGrph{NewIndex}{1}.LineWidth=2;
    totalJouleGrph{NewIndex}{1}.LineStyle='-';
    totalJouleGrph{NewIndex}{1}.Marker     ='^';
    totalJouleGrph{NewIndex}{1}.Color     = [0 114 189]/256;
    totalJouleGrph{NewIndex}{1}.MarkerFaceColor     = [0 114 189]/256;
    formatterFigure4Paper('Double','2x2');
    ax=convertFigXAxisToElecDeg(0);
end

