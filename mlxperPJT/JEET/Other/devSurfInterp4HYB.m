%% Table of Contents
%% Create the Flux Density Fit 
%% Plot
%% test 4D Fitting gp
%% Radial Position 별로 B값 추출

load('wireTable_SCL_TS_18krpm_case28.mat');
triangulations = partitionedTriangulation(WireTable);
grey=greyColor();

DT=cell(height(WireTable),1);
%% Create the Flux Density Fit 
for slotIndex=1:height(WireTable)
  DT{slotIndex}=mkdelauyTByPartTable(WireTable,'TtileTableByElerow', slotIndex);
end
WireTable.DT =DT;
% WireTable.BthfitResult=WireTable.BthfitResult(:,241:480);
% save('wireTableDT_SCL_TS_18krpm_case28.mat','WireTable')
load('wireTableDT_SCL_TS_18krpm_case28.mat')

n = 1:4;  % 1~4까지 n

% 결과 확인
%% Radial Position 별로 B값 추출
% Position 산정
for SlotIndex=1:height(WireTable)
    [theta{SlotIndex},Rpos{SlotIndex}]    =cart2pol(WireTable.RtileTableByElerow{SlotIndex}.x,WireTable.RtileTableByElerow{SlotIndex}.y);
    minRPos(SlotIndex)                    =min(Rpos{SlotIndex});
    mintheta(SlotIndex)                   =min(theta{SlotIndex});
    maxtheta(SlotIndex)                   =max(theta{SlotIndex});
end
[tempRPos,sorIdx]=sort(minRPos);
% mintheta        =mintheta(sorIdx);
% maxtheta        =maxtheta(sorIdx);
for SlotIndex=1:len(minRPos)-1
    plotCircle(minRPos(SlotIndex),[mintheta(SlotIndex) maxtheta(SlotIndex)],'k');
    hold on
end
%% RightX ,RightY 4 SubLine
WireTabNames=WireTable.Name;
SlotNumberCell=extractBetween(WireTabNames,'Slot','/Wire');
SlotNumberList=unique(SlotNumberCell);
WireNumberCell=extractAfter(WireTabNames,'/Wire');
WireNumberList=unique(WireNumberCell);


%% Layer별로 subline개수 결정
UniRPos=uniquetol(tempRPos,1e-2);
WireLayerInterGap=(UniRPos(3)-UniRPos(2));   %% 슬롯가장안쪽(R이 큰거)부터 번호시작(권선 넣는순서)
if WireLayerInterGap>0
UniRPos=flipud(UniRPos);  
WireLayerInterGap=(UniRPos(2)-UniRPos(3));
end
WireLayerInterGap=abs((UniRPos(2)-UniRPos(3)));

for slotIndex=1:height(WireTable)
hold on 
triplot(WireTable.DT{slotIndex})

end

for SlotIndex=1:height(WireTable)
    subLineRPos=[];
    subLineRightThetaRange=[];
    subLineLeftThetaRange=[];
    RightX          =[];
    RightY          =[];
    LeftX           =[];
    LeftY           =[];
    LayerNumber = str2double(WireNumberCell{SlotIndex});
    % SlotNumber  = SlotNumberCell{SlotIndex};
    % SlotIdx4Theta     = find(strcmp(SlotNumberList,SlotNumber));
     for subLine=1:1*LayerNumber
        lineSC = 1.1 - (subLine - 1) * (1.1 - 1) / (5 - 1);  % n이 1일 때는 1.001, 4일 때는 1
        % inverlineSC = 0.997 - (subLine - 1) * (0.997  - 1) / (4 - 1);  % n이 1일 때는 1.001, 4일 때는 1
        % scatter(subLine,lineSC,'k')
       % hold on
        % scatter(subLine,inverlineSC,'r')
        subLineRPos(subLine)           =minRPos(SlotIndex)+WireLayerInterGap*subLine/10;
        midLineTheta = (maxtheta(SlotIndex)+mintheta(SlotIndex))/2;  % 최대 각도
        % right
        [reducedMinTheta,~]=reduceWidthpolar(mintheta(SlotIndex),midLineTheta,lineSC);
        subLineRightThetaRange{subLine}=[reducedMinTheta midLineTheta];
        %left
        [~,reducedMaxTheta]=reduceWidthpolar(midLineTheta,maxtheta(SlotIndex),lineSC);
        subLineLeftThetaRange{subLine} =[midLineTheta reducedMaxTheta]; 
        [RightX{subLine},RightY{subLine}]=plotCircle(subLineRPos(subLine),subLineRightThetaRange{subLine} ,'r','--');
        hold on
        [LeftX{subLine}, LeftY{subLine}] =plotCircle(subLineRPos(subLine),subLineLeftThetaRange{subLine},'b','--');
     end
    WireTable.subLineRPos{SlotIndex}=  subLineRPos';
    WireTable.subLineRightThetaRange{SlotIndex}=  subLineRightThetaRange';
    WireTable.subLineLeftThetaRange{SlotIndex}=   subLineLeftThetaRange';
    WireTable.RightX{SlotIndex}=RightX;
    WireTable.RightY{SlotIndex}=RightY;
    WireTable.LeftX{SlotIndex} =LeftX;
    WireTable.LeftY{SlotIndex} =LeftY;
    % hold on
end


%% WireTable 2 WireFitTable
propNames=WireTable.Properties.VariableNames';
WireFitTable=WireTable(:,{'Name','subLineRPos','elementCentersTable','RightX','RightY','LeftX','LeftY','DT'});
%% Value Table
tempValueTable=WireTable(:,{'RtileTableByElerow','TtileTableByElerow'});
propNameofValue=tempValueTable.RtileTableByElerow{1}.Properties.VariableNames;
BoolSteps=contains(propNameofValue,'Step');
stepsName=propNameofValue(BoolSteps);
newNumsteps=len(stepsName)/2;
Numvars=width(tempValueTable);
newVarName=[cellstr([repmat('Step',newNumsteps+1,1) num2str([1:newNumsteps+1]')])]';
newVarName=strrep(newVarName,' ','');
%% time reduce
tempValueTable=WireTable(:,{'RtileTableByElerow','TtileTableByElerow'});
for SlotIndex=1:height(tempValueTable)
    for varIndex=1:Numvars
        tempsubValueTable=tempValueTable.(varIndex){SlotIndex};
        tempStepValue    =tempsubValueTable{:,BoolSteps};
        filteredstepValue        =tempStepValue(:,newNumsteps:end);
        newStepTable     =array2table(filteredstepValue,"VariableNames",newVarName);
        tempInfoTable    =tempsubValueTable(:,~BoolSteps);
        tempValueTable.(varIndex){SlotIndex}=[tempInfoTable newStepTable];
    end
end
WireFitTable=[WireFitTable tempValueTable];


propNameofValue=WireFitTable.RtileTableByElerow{1}.Properties.VariableNames;
BoolSteps=contains(propNameofValue,'Step');
stepsName=propNameofValue(BoolSteps);
newNumsteps=len(stepsName);
%% fit으로부터 subLine별로 추출
for slotIndex = 1:height(WireFitTable)
    NumSubLine = len(WireFitTable.subLineRPos{slotIndex});
    
    Br3DRightArray = cell(NumSubLine, 1);
    Bt3DRightArray = cell(NumSubLine, 1);
    Br3DLeftArray  = cell(NumSubLine, 1);
    Bt3DLeftArray  = cell(NumSubLine, 1);
    
    for subLine = 1:NumSubLine
        % pxr의 길이에 맞춰서 저장할 배열 초기화
        Br3DRightArray{subLine} = zeros(newNumsteps, length(WireFitTable.RightX{slotIndex}{subLine}));
        Bt3DRightArray{subLine} = zeros(newNumsteps, length(WireFitTable.RightX{slotIndex}{subLine}));
        Br3DLeftArray{subLine}  = zeros(newNumsteps, length(WireFitTable.LeftX{slotIndex}{subLine}));
        Bt3DLeftArray{subLine}  = zeros(newNumsteps, length(WireFitTable.LeftX{slotIndex}{subLine}));
        
        for stepIndex = 1:newNumsteps
            Brvalues = WireFitTable.RtileTableByElerow{slotIndex}.(sprintf('Step%d', stepIndex));
            Btvalues = WireFitTable.TtileTableByElerow{slotIndex}.(sprintf('Step%d', stepIndex));
            
            % 좌표 추출
            pxr = WireFitTable.RightX{slotIndex}{subLine}';
            pyr = WireFitTable.RightY{slotIndex}{subLine}';
            pxl = WireFitTable.LeftX{slotIndex}{subLine}';
            pyl = WireFitTable.LeftY{slotIndex}{subLine}';
            
            % 물리량 보간 후 배열에 저장
            Br3DRightArray{subLine}(stepIndex, :) = getdeluayInterpPointValue(pxr, pyr, Brvalues, WireFitTable.DT{slotIndex});
            Bt3DRightArray{subLine}(stepIndex, :) = getdeluayInterpPointValue(pxr, pyr, Btvalues, WireFitTable.DT{slotIndex});
            Br3DLeftArray{subLine}(stepIndex, :)  = getdeluayInterpPointValue(pxl, pyl, Brvalues, WireFitTable.DT{slotIndex});
            Bt3DLeftArray{subLine}(stepIndex, :)  = getdeluayInterpPointValue(pxl, pyl, Btvalues, WireFitTable.DT{slotIndex});
        end
    end
    
    % 최종 결과 저장
    WireFitTable.Br3DRightArray{slotIndex} = Br3DRightArray;
    WireFitTable.Bt3DRightArray{slotIndex} = Bt3DRightArray;
    WireFitTable.Br3DLeftArray{slotIndex}  = Br3DLeftArray;
    WireFitTable.Bt3DLeftArray{slotIndex}  = Bt3DLeftArray;
end
% end

%% Plot surf
propNames=WireFitTable.Properties.VariableNames';
for slotIndex=1:height(WireFitTable)
    LayerNumber=WireNumberCell{slotIndex};
    SlotNumber= SlotNumberCell{slotIndex};
    figure('Name',['slot',SlotNumber,'Layer',LayerNumber])
    NumsubLine=len(WireFitTable.RightX{slotIndex});
    for sublineIndex=1:NumsubLine
        [theta,r] =cart2pol(WireFitTable.RightX{slotIndex}{sublineIndex},WireFitTable.RightY{slotIndex}{sublineIndex});
        subplot(1,NumsubLine,sublineIndex)
        surfData=[WireFitTable.Br3DRightArray{slotIndex}{sublineIndex}];
        surf(rad2deg(theta),[1:newNumsteps],surfData,'EdgeColor','none','DisplayName',['SubLine',num2str(sublineIndex)])
        hold on
    end
end
% 
save('WireFitTables_SCL_TS_18krpm_case28.mat','WireFitTable')
delete('WireFitTables_SCL_TS_18krpm_case28.mat')
%% FFT Plot

fft_1d_gif(Br3DLeft',4)
[mag_fft_V_c]=plot_2d_fft_positive([Br3DLeft Bt3DRight]',4,'[T]')
[mag_fft_V_c]=plot_2d_fft_positive(Bt3DLeft',4,'[T]')
%% HYB계산

RightX{LayerIndex,SlotIndex,1}'