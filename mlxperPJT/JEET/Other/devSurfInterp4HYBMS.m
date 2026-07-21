%% Table of Contents
% load WireTable 
% Create the Flux Density Fit 
% Radial Position 별로 B값 추출
% RightX ,RightY 4 SubLine
% Layer별로 subline개수 결정
% WireTable 2 WireFitTable
% subLine
% fit으로부터 subLine별로 추출

%% load WireTable 
% D:\KangDH\Emlab_emach\mlxperPJT\JEET\dev_plot3DVectorB_4_MS_general.m
matFileList    =findMatFiles(pwd)'                              
matFileList    =matFileList(contains(matFileList,'wire'))           
MSmatFileList  =matFileList(contains(matFileList,'MS'))         
REFmatFileList =MSmatFileList(contains(MSmatFileList,'SCL'))            
REFmatFileList =REFmatFileList(contains(REFmatFileList,'MagB'))
% 2026-07-20: 아래 이름기반 필터(주석)는 산출물(*FitwithDT.mat)을 걸러내려던 것이나
%   주석 상태여서 산출물까지 입력으로 읽혔고, 그 파일엔 WireTable 이 없어
%   27행 load 직후 28행 height(WireTable) 에서 미정의 변수 오류가 났다.
%   → 이름 대신 "파일 안에 WireTable 이 실제로 있는지"로 판정한다(견고).
%   실측(2026-07-20): *_wireTable.mat = WireTable 보유 / *DenseFitwithDT.mat = WireFitTable 만.
% REFmatFileList=REFmatFileList(~contains(REFmatFileList,'DT'))
hasWireTable   =cellfun(@(f) any(strcmp({whos('-file',f).name},'WireTable')), REFmatFileList);
if ~any(hasWireTable)
    error('devSurfInterp4HYBMS:noInput', ...
          'WireTable 을 가진 .mat 이 없습니다. pwd=%s (대상 %d개 검사)', ...
          pwd, numel(REFmatFileList));
end
fprintf('[filter] WireTable 보유 %d / 후보 %d 개 선택\n', sum(hasWireTable), numel(REFmatFileList));
REFmatFileList =REFmatFileList(hasWireTable);

[~,MatfileNames,~]=fileparts(REFmatFileList)
timeStepReducedFactor=1;  % 480 step -> 240 = 2
% triangulations = partitionedTriangulation(WireTable);
grey=greyColor();
%% Create the Flux Density Fit 
for caseIndex=1:len(REFmatFileList)
    clear WireTable
    load(REFmatFileList{caseIndex});
    for slotIndex=1:height(WireTable)
        DT{slotIndex}=mkdelauyTByPartTable(WireTable,'TtileTableByElerow', slotIndex);
    end
    WireTable.DT =DT';
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

% for slotIndex=1:height(WireTable)
% hold on 
% triplot(WireTable.DT{slotIndex})
% 
% end

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
if ~timeStepReducedFactor==1
    propNames=WireTable.Properties.VariableNames';
    WireFitTable=WireTable(:,{'Name','subLineRPos','elementCentersTable','RightX','RightY','LeftX','LeftY','DT'});
    %% Value Table
    tempValueTable=WireTable(:,{'RtileTableByElerow','TtileTableByElerow'});
    propNameofValue=tempValueTable.RtileTableByElerow{1}.Properties.VariableNames;
    BoolSteps=contains(propNameofValue,'Step');
    stepsName=propNameofValue(BoolSteps);
    newNumsteps=len(stepsName)/timeStepReducedFactor;
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
else
WireFitTable=WireTable(:,{'Name','subLineRPos','elementCentersTable','RightX','RightY','LeftX','LeftY','RtileTableByElerow','TtileTableByElerow','DT'});
end
%% subLine
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
   save([MatfileNames{caseIndex},'FitwithDT.mat'],'WireFitTable')
end

%% test 4D Fitting gp
%% Radial Position 별로 B값 추출