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
NumSubline=11;
matFileList    =findMatFiles(pwd)';                              
matFileList    =matFileList(contains(matFileList,'wire'));           
MSmatFileList  =matFileList(contains(matFileList,'MS'));         
REFmatFileList =MSmatFileList(contains(MSmatFileList,'SCL'));            
REFmatFileList =REFmatFileList(contains(REFmatFileList,'MagB'));         
REFmatFileList=REFmatFileList(~contains(REFmatFileList,'DT'));

[~,MatfileNames,~]=fileparts(REFmatFileList);
timeStepReducedFactor=1;  % 480 step -> 240 = 2
% triangulations = partitionedTriangulation(WireTable);
grey=greyColor();

% parpool;  % 병렬 풀 시작 (필요한 경우)

% 결과를 저장할 셀 배열 선언
WireFitTableCell = cell(1, 30);

parfor caseIndex = 1:30  % 병렬 처리
    % 초기화
    tempStruct = load(REFmatFileList{caseIndex});  % 데이터 로드
    WireTable = tempStruct.WireTable;              % WireTable 추출
    
    %% Radial Position 별로 B값 추출
    theta = cell(height(WireTable),1);
    Rpos = cell(height(WireTable),1);
    minRPos = zeros(height(WireTable),1);
    maxRPos = zeros(height(WireTable),1);
    mintheta = zeros(height(WireTable),1);
    maxtheta = zeros(height(WireTable),1);
    for SlotIndex = 1:height(WireTable)
        nodexPos = WireTable.NodeTable{SlotIndex}.nodeCoords(:,1);
        nodeyPos = WireTable.NodeTable{SlotIndex}.nodeCoords(:,2);
        [theta{SlotIndex}, Rpos{SlotIndex}] = cart2pol(nodexPos, nodeyPos);
        minRPos(SlotIndex) = min(Rpos{SlotIndex});
        maxRPos(SlotIndex) = max(Rpos{SlotIndex});
        mintheta(SlotIndex) = min(theta{SlotIndex});
        maxtheta(SlotIndex) = max(theta{SlotIndex});
    end
    
    %% RightX, RightY 4 SubLine 설정
    WireTabNames = WireTable.Name;
    SlotNumberCell = extractBetween(WireTabNames,'Slot','/Wire');
    SlotNumberList = unique(SlotNumberCell);
    WireNumberCell = extractAfter(WireTabNames,'/Wire');
    WireNumberList = unique(WireNumberCell);
    
    %% Layer 별로 subline 개수 결정
    UniRPos = uniquetol(minRPos, 1e-2);
    if length(UniRPos) > 2
        WireLayerInterGap = abs(UniRPos(2) - UniRPos(3));
    end

    %% SubLine 및 테이블 업데이트
    for SlotIndex = 1:height(WireTable)
        subLineRPos = [];
        subLineRightThetaRange = [];
        subLineLeftThetaRange = [];
        RightX = [];
        RightY = [];
        LeftX = [];
        LeftY = [];
        
        LayerNumber = str2double(WireNumberCell{SlotIndex});
        SlotHeight = maxRPos(SlotIndex) - minRPos(SlotIndex);
        subLineWidth = SlotHeight / NumSubline;
        subLineRPos = [minRPos(SlotIndex) * 1.001 : subLineWidth : maxRPos(SlotIndex) * 0.9999];

        for subLine = 1:NumSubline
            lineSC = 1.1;  % Subline의 크기 비율 설정
            midLineTheta = (maxtheta(SlotIndex) + mintheta(SlotIndex)) / 2;

            % Right Subline 설정
            [reducedMinTheta, ~] = reduceWidthpolar(mintheta(SlotIndex), midLineTheta, lineSC);
            subLineRightThetaRange{subLine} = [reducedMinTheta, midLineTheta];

            % Left Subline 설정
            [~, reducedMaxTheta] = reduceWidthpolar(midLineTheta, maxtheta(SlotIndex), lineSC);
            subLineLeftThetaRange{subLine} = [midLineTheta, reducedMaxTheta];

            % Circle 그리기 (Right/Left)
            [RightX{subLine}, RightY{subLine}] = plotCircle(subLineRPos(subLine), subLineRightThetaRange{subLine}, 'r', '--');
            [LeftX{subLine}, LeftY{subLine}] = plotCircle(subLineRPos(subLine), subLineLeftThetaRange{subLine}, 'b', '--');
            close all
        end

        WireTable.subLineRPos{SlotIndex} = subLineRPos';
        WireTable.subLineRightThetaRange{SlotIndex} = subLineRightThetaRange';
        WireTable.subLineLeftThetaRange{SlotIndex} = subLineLeftThetaRange';
        WireTable.RightX{SlotIndex} = RightX;
        WireTable.RightY{SlotIndex} = RightY;
        WireTable.LeftX{SlotIndex} = LeftX;
        WireTable.LeftY{SlotIndex} = LeftY;
    end

    %% WireFitTable 생성 및 subLine별로 데이터 추출
    WireFitTable = WireTable(:,{'Name','subLineRPos','elementCentersTable','RightX','RightY','LeftX','LeftY','RtimeTableByElerow','TtimeTableByElerow','DT'});
    propNameofValue = WireFitTable.RtimeTableByElerow{1}.Properties.VariableNames;
    BoolSteps = contains(propNameofValue, 'Step');
    stepsName = propNameofValue(BoolSteps);
    newNumsteps = length(stepsName);

    %% subLine별로 B값 추출
    for slotIndex = 1:height(WireFitTable)
        NumSubLine = length(WireFitTable.subLineRPos{slotIndex});

        Br3DRightArray = cell(NumSubLine, 1);
        Bt3DRightArray = cell(NumSubLine, 1);
        Br3DLeftArray  = cell(NumSubLine, 1);
        Bt3DLeftArray  = cell(NumSubLine, 1);

        for subLine = 1:NumSubLine
            for stepIndex = 1:newNumsteps
                Brvalues = WireFitTable.RtimeTableByElerow{slotIndex}.(sprintf('Step%d', stepIndex));
                Btvalues = WireFitTable.TtimeTableByElerow{slotIndex}.(sprintf('Step%d', stepIndex));

                pxr = WireFitTable.RightX{slotIndex}{subLine}';
                pyr = WireFitTable.RightY{slotIndex}{subLine}';
                pxl = WireFitTable.LeftX{slotIndex}{subLine}';
                pyl = WireFitTable.LeftY{slotIndex}{subLine}';

                Br3DRightArray{subLine}(stepIndex, :) = getdeluayInterpPointValue(pxr, pyr, Brvalues, WireFitTable.DT{slotIndex});
                Bt3DRightArray{subLine}(stepIndex, :) = getdeluayInterpPointValue(pxr, pyr, Btvalues, WireFitTable.DT{slotIndex});
                Br3DLeftArray{subLine}(stepIndex, :) = getdeluayInterpPointValue(pxl, pyl, Brvalues, WireFitTable.DT{slotIndex});
                Bt3DLeftArray{subLine}(stepIndex, :) = getdeluayInterpPointValue(pxl, pyl, Btvalues, WireFitTable.DT{slotIndex});
            end
        end

        WireFitTable.Br3DRightArray{slotIndex} = Br3DRightArray;
        WireFitTable.Bt3DRightArray{slotIndex} = Bt3DRightArray;
        WireFitTable.Br3DLeftArray{slotIndex} = Br3DLeftArray;
        WireFitTable.Bt3DLeftArray{slotIndex} = Bt3DLeftArray;
    end

    % 병렬 작업 결과 저장
    WireFitTableCell{caseIndex} = WireFitTable;
end

delete(gcp('nocreate'));  % 병렬 풀 종료

% 병렬 작업 완료 후 순차적으로 저장
for caseIndex = 1:30
    WireFitTable = WireFitTableCell{caseIndex};
    save([MatfileNames{caseIndex}, 'DenseFitwithDT.mat'], 'WireFitTable');
end


% D:\KangDH\Emlab_emach\mlxperPJT\JEET\devmkBSFDTable.m