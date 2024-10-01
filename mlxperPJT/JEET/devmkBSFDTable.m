% D:\KangDH\Emlab_emach\mlxperPJT\JEET\devSurfInterp4HYBMS.m
clear



%% get Dta
matFileList=findMatFiles(pwd)';
matFileList=matFileList(contains(matFileList,'wire'));
MSmatFileList=matFileList(contains(matFileList,'MS'));
REFmatFileList=MSmatFileList(contains(MSmatFileList,'SCL'));
REFmatFileList=REFmatFileList(contains(REFmatFileList,'MagB'));
REFDTmatFileList=REFmatFileList(contains(REFmatFileList,'DT'));
[~,MatfileNames,~]=fileparts(REFDTmatFileList);
%% def
load(MatfileNames{1})
WireLayerInterGap=WireFitTable.subLineRPos{2}(2)-WireFitTable.subLineRPos{2}(1);
BrData=WireFitTable.Bt3DLeftArray{1}{:};
BrDataSize       =size(BrData);
WireWidth_division=BrDataSize(2);
TimeSteps=BrDataSize(1);
refdimensions=[3.7 1.6]*2;



parpool;  % 병렬 풀 시작

% 결과를 저장할 셀 배열 선언
BrRcell = cell(len(MatfileNames), 1);
BtRcell = cell(len(MatfileNames), 1);
BrLcell = cell(len(MatfileNames), 1);
BtLcell = cell(len(MatfileNames), 1);

parfor caseIndex = 1:len(MatfileNames)  % 병렬 처리
    % 초기화
    tempStrct=load(MatfileNames{caseIndex,1})
    WireFitTable=tempStrct.WireFitTable
    % 기본 정의 및 초기화
    WireTabNames = WireFitTable.Name;
    SlotNumberCell = extractBetween(WireTabNames, 'Slot', '/Wire');
    SlotNumberList = unique(SlotNumberCell);
    WireNumberCell = extractAfter(WireTabNames, '/Wire');
    WireNumberList = unique(WireNumberCell);

    % B SFD
    BSFDrrPerSLot = cell(height(WireFitTable), 1);
    BSFDtrPerSLot = cell(height(WireFitTable), 1);
    BSFDrlPerSLot = cell(height(WireFitTable), 1);
    BSFDtlPerSLot = cell(height(WireFitTable), 1);

    for slotWireIDX = 1:height(WireFitTable)
        NumsubLine = len(WireFitTable.RightX{slotWireIDX});
        BSfDrr = cell(NumsubLine, 1);
        BSfDtr = cell(NumsubLine, 1);
        BSfDrl = cell(NumsubLine, 1);
        BSfDtl = cell(NumsubLine, 1);
        for sublineIndex = 1:NumsubLine
            BSfDrr{sublineIndex} = (WireFitTable.Br3DRightArray{slotWireIDX}{sublineIndex}).^2;
            BSfDtr{sublineIndex} = (WireFitTable.Bt3DRightArray{slotWireIDX}{sublineIndex}).^2;
            BSfDrl{sublineIndex} = (WireFitTable.Br3DLeftArray{slotWireIDX}{sublineIndex}).^2;
            BSfDtl{sublineIndex} = (WireFitTable.Bt3DLeftArray{slotWireIDX}{sublineIndex}).^2;
        end
        BSFDrrPerSLot{slotWireIDX} = BSfDrr;
        BSFDtrPerSLot{slotWireIDX} = BSfDtr;
        BSFDrlPerSLot{slotWireIDX} = BSfDrl;
        BSFDtlPerSLot{slotWireIDX} = BSfDtl;
    end
    WireFitTable.BSFDrrPerSLot = BSFDrrPerSLot;
    WireFitTable.BSFDtrPerSLot = BSFDtrPerSLot;
    WireFitTable.BSFDrlPerSLot = BSFDrlPerSLot;
    WireFitTable.BSFDtlPerSLot = BSFDtlPerSLot;

    % BSFD FFT
    BrR = cell(height(WireFitTable), height(WireFitTable));
    BtR = cell(height(WireFitTable), height(WireFitTable));
    BrL = cell(height(WireFitTable), height(WireFitTable));
    BtL = cell(height(WireFitTable), height(WireFitTable));

    for slotWireIDX = 1:height(WireFitTable)
        NumsubLine = len(WireFitTable.RightX{slotWireIDX});
        for sublineIndex = 1:NumsubLine
            [BrL{slotWireIDX, sublineIndex}, ~, ~] = getFFT1Dset(WireFitTable.BSFDrlPerSLot{slotWireIDX}{sublineIndex}, 1);
            [BrR{slotWireIDX, sublineIndex}, ~, ~] = getFFT1Dset(WireFitTable.BSFDrrPerSLot{slotWireIDX}{sublineIndex}, 1);
            [BtL{slotWireIDX, sublineIndex}, ~, ~] = getFFT1Dset(WireFitTable.BSFDtlPerSLot{slotWireIDX}{sublineIndex}, 1);
            [BtR{slotWireIDX, sublineIndex}, ~, ~] = getFFT1Dset(WireFitTable.BSFDtrPerSLot{slotWireIDX}{sublineIndex}, 1);
        end
    end

    % 결과 저장
    BrRcell{caseIndex, 1} = BrR;
    BtRcell{caseIndex, 1} = BtR;
    BrLcell{caseIndex, 1} = BrL;
    BtLcell{caseIndex, 1} = BtL;
end

delete(gcp('nocreate'));  % 병렬 풀 종료

% dq Table 
BdisSFDTableName = {'MatFileName', 'BrRcell', 'BtRcell', 'BrLcell', 'BtLcell'};
BdisSFDTable = cell2table([MatfileNames, BrRcell, BtRcell, BrLcell, BtLcell], 'VariableNames', BdisSFDTableName);
caseNumber = extractBetween(BdisSFDTable.MatFileName, 'Case', '_MagB');
caseNumber = cellfun(@(x) str2double(x), caseNumber);
BdisSFDTable.caseIndex = caseNumber;
BdisSFDTable = sortrows(BdisSFDTable, "caseIndex", "ascend");

% 결과 저장
save('coeffiSCLBdisSFDTableV1.mat', 'BdisSFDTable')