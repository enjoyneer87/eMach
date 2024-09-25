

%% Create the Flux Density Fit 
for StepList=241:480
    for slotIndex=1:height(WireTable)
      DT{slotIndex,StepList-240}=mkTimedelauyTByPartTable(WireTable,'TtileTableByElerow', slotIndex, StepList);
    end
end
WireTable.DT =DT;
WireTable.BthfitResult=WireTable.BthfitResult(:,241:480);

% %% Plot
% for slotIndex=1:height(WireTable)
%     for SteIndex=241:20:480
%     hold on
%     Surf     =BrfitResult{slotIndex,SteIndex}(Xq{slotIndex,SteIndex},Yq{slotIndex,SteIndex});
%     surfGriddata(Xq{slotIndex,SteIndex},Yq{slotIndex,SteIndex},Surf)
%     end
% end


%% test 4D Fitting gp
StepList=241:30:480;
for SteIndex=1:len(StepList)
    fitResult{SteIndex}=BrfitResult{1,StepList(SteIndex)};
end
[model, fID,fIQ]    = fitTrivariateByTPS(fitResult, StepList, [20 20]);
compareRBFwithfitresult(model,fitResult,241:30:480)


%% Radial Position 별로 B값 추출
% Position 산정
for SlotIndex=1:height(WireTable)-1
    [theta{SlotIndex},Rpos{SlotIndex}]    =cart2pol(WireTable.RtileTableByElerow{SlotIndex}.x,WireTable.RtileTableByElerow{SlotIndex}.y);
    minRPos(SlotIndex)                    =min(Rpos{SlotIndex});
    mintheta(SlotIndex)                   =min(theta{SlotIndex});
    maxtheta(SlotIndex)                   =max(theta{SlotIndex});
end
[minRPos,sorIdx]=sort(minRPos);
mintheta        =mintheta(sorIdx);
maxtheta        =maxtheta(sorIdx);
for SlotIndex=1:len(minRPos)-1
    plotCircle(minRPos(SlotIndex),[mintheta(SlotIndex) maxtheta(SlotIndex)],'k');
    hold on
end
UniRPos=uniquetol(minRPos,1e-2);
uniMint=uniquetol(mintheta,1e-2);
uniMaxt=uniquetol(maxtheta,1e-2);
%% RightX ,RightY 4 SubLine
WireTabNames=WireTable.Name;
SlotNumberCell=extractBetween(WireTabNames,'Slot','/Wire');
SlotNumberList=unique(SlotNumberCell);
WireNumberCell=extractAfter(WireTabNames,'/Wire');
WireNumberList=unique(WireNumberCell);
%% subline
RightX=[];
RightY=[];
LeftX=[];
LeftY=[];
subLineRPos=[];
subLineRightThetaRange=[];
subLineLeftThetaRange=[];

%% Layer별로 subline개수 결정
WireLayerInterGap=(UniRPos(3)-UniRPos(2));
if WireLayerInterGap<0
UniRPos=flipud(UniRPos)';
end

for SlotIndex=1:height(WireTable)
    subLineRPos=[];
    subLineRightThetaRange=[];
    subLineLeftThetaRange=[];
    RightX          =[];
    RightY          =[];
    LeftX           =[];
    LeftY           =[];
    LayerNumber=str2double(WireNumberCell{SlotIndex});
    SlotNumber= SlotNumberCell{SlotIndex};
    SlotIdx=find(strcmp(SlotNumberList,SlotNumber));
     for subLine=1:1*LayerNumber
        subLineRPos(end+1)          =UniRPos(LayerNumber)+WireLayerInterGap*subLine/10;
        subLineRightThetaRange{end+1}=[uniMint(SlotIdx) (uniMaxt(SlotIdx)-uniMint(SlotIdx))/2+uniMint(SlotIdx)];
        subLineLeftThetaRange{end+1} =[(uniMaxt(SlotIdx)-uniMint(SlotIdx))/2+uniMint(SlotIdx) uniMaxt(SlotIdx)]; 
        [RightX{subLine},RightY{subLine}]=plotCircle(subLineRPos(end),subLineRightThetaRange{end} ,'r','--');
        [LeftX{subLine}, LeftY{subLine}] =plotCircle(subLineRPos(end),subLineLeftThetaRange{end},'b','--');
     end
    WireTable.subLineRPos{SlotIndex}=  subLineRPos';
    WireTable.subLineRightThetaRange{SlotIndex}=  subLineRightThetaRange';
    WireTable.subLineLeftThetaRange{SlotIndex}=  subLineLeftThetaRange';
    WireTable.RightX{SlotIndex}=RightX;
    WireTable.RightY{SlotIndex}=RightY;
    WireTable.LeftX{SlotIndex} =LeftX;
    WireTable.LeftY{SlotIndex} =LeftY;
    hold on
end

%% fit으로부터 subLine별로 추출
for slotIndex=1:height(WireTable)
    NumSubLine=len(WireTable.subLineRPos{slotIndex});
    Br3DRightCell       =cell(NumSubLine,1);
    Bt3DRightCell       =cell(NumSubLine,1);
    Br3DLeftCell        =cell(NumSubLine,1);
    Bt3DLeftCell        =cell(NumSubLine,1);
    for subLine=1:NumSubLine
        Br3DRight=cell(240,1)   ;
        Bt3DRight=cell(240,1)   ;
        Br3DLeft =cell(240,1)   ; 
        Bt3DLeft =cell(240,1)   ; 
        for StepList=1:240
           Br3DRight{StepList,1}=  WireTable.BrfitResult{slotIndex,StepList}(WireTable.RightX{SlotIndex} {subLine} , WireTable.RightY{SlotIndex}{subLine}   )'   ;     
           Bt3DRight{StepList,1}=  WireTable.BthfitResult{slotIndex,StepList}(WireTable.RightX{SlotIndex}{subLine} , WireTable.RightY{SlotIndex}{subLine}   )'   ;     
           Br3DLeft {StepList,1}=  WireTable.BrfitResult{slotIndex,StepList}(WireTable.LeftX{SlotIndex}  {subLine} , WireTable.LeftY{SlotIndex} {subLine}   )'   ; 
           Bt3DLeft {StepList,1}=  WireTable.BthfitResult{slotIndex,StepList}(WireTable.LeftX{SlotIndex} {subLine} , WireTable.LeftY{SlotIndex} {subLine}   )'   ; 
        end
        Br3DRightCell{subLine}           =Br3DRight ;
        Bt3DRightCell{subLine}           =Bt3DRight ;
        Br3DLeftCell{subLine}            =Br3DLeft  ;
        Bt3DLeftCell{subLine}            =Bt3DLeft  ;
    end
    WireTable.Br3DRightCell{slotIndex}             =Br3DRightCell;
    WireTable.Bt3DRightCell{slotIndex}             =Bt3DRightCell;
    WireTable.Br3DLeftCell {slotIndex}             =Br3DLeftCell;
    WireTable.Bt3DLeftCell {slotIndex}             =Bt3DLeftCell;
end
% end