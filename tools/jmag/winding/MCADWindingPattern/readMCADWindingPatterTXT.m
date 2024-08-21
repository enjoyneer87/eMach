function [McadWindingPatternTable, MachineInfo]=readMCADWindingPatterTXT(windingPatternTxtPath)
    
    %% MotFileName
    % clear opts
    % 
    % opts = detectImportOptions(windingPatternTxtPath,'VariableNamingRule','modify');
    % opts.DataLines = [1 8]; % fist block of data
    % opts = detectImportOptions(windingPatternTxtPath, 'Delimiter', delimiter,'VariableNamingRule','modify');
    % data4Header=readtable(windingPatternTxtPath,opts);
    % isFileNameRow=contains(data4Header{:,:},'Model_File');
    % FileNameCell=data4Header{isFileNameRow,:};
    % [MotFileName]=extractAfter(FileNameCell{:},'=');

    %% DataRead    
    delimiter='=';
    opts = detectImportOptions(windingPatternTxtPath, 'Delimiter', delimiter,'VariableNamingRule','modify');
    VariableTypes      = repmat({'char'}, 1, length(opts.VariableTypes));
    opts.VariableTypes=VariableTypes;
    data = readtable(windingPatternTxtPath,opts);
    % pat = ~textBoundary  + ~textBoundary;
     
    % lastWords = extract(data.Notes{1},pat)
    %% Header 
    %%[Calc_Options]
    isFileNameRow=contains(data{:,1},'[Calc_Options]');
    Calc_OptionsIndex=find(isFileNameRow);
    %%[Dimensions]
    isFileNameRow=contains(data{:,1},'[Dimensions]');
    DimensionsIndex=find(isFileNameRow); 
    %%[Magnetics]
    isFileNameRow=contains(data{:,1},'[Magnetics]');
    MagneticsIndex=find(isFileNameRow);
    %[Magnetic_Winding]
    isFileNameRow=contains(data{:,1},'[Magnetic_Winding]');
    Magnetic_WindingIndex=find(isFileNameRow);    
    %% SplitTable
    Calc_Options=data(Calc_OptionsIndex+1:DimensionsIndex-1,:);
    Dimensions=data(DimensionsIndex+1:MagneticsIndex-1,:);
    Magnetics=data(MagneticsIndex+1:Magnetic_WindingIndex-1,:);
    Magnetic_Winding=data(Magnetic_WindingIndex+1:end,:);
    Magnetic_Winding.Properties.VariableNames={'Names','ValueData'};
    ValueTable=Magnetic_Winding.ValueData;
    ValueTable=cell2table(ValueTable);
    
    SplitofRow=[];
    PhaseNumber=[];
    ParallelPathNumber=[];
    CoilNumber=[];
    TypeofData=[];
    for TableIndex=1:height(Magnetic_Winding)
    % ParallelPathNumber(TableIndex)=extractBetween(Magnetic_Winding{1,1},"Path_","_");
        NewSplitofRow=strsplit(Magnetic_Winding.Names{TableIndex},"_");
        SplitofRow=[SplitofRow;NewSplitofRow];
        % PhaseNumber
        tempPhaseNumber=extractBefore(SplitofRow{TableIndex,2},'Path'); 
        PhaseNumber(TableIndex,1)=str2num(tempPhaseNumber);    
        % ParallelPathNumber
        ParallelPathNumber(TableIndex,1)=str2num(SplitofRow{TableIndex,3});    
        % CoilNumber
        tempCellCoilNumber=extractBetween(SplitofRow{TableIndex,4},'[',']'); 
        CoilNumber(TableIndex,1)=str2num(tempCellCoilNumber{:});
        % TypeofData
        TypeofrowData=extractBefore(SplitofRow{TableIndex,4},'['); 
        TypeofData=[TypeofData;{TypeofrowData}];
    end

    tempPhaseNumberTable        =table(PhaseNumber,'VariableNames',"PhaseNumber");
    tempParallelPathNumberTable =table(ParallelPathNumber,'VariableNames',"ParallelPathNumber");
    tempTypeofData              =cell2table(TypeofData,'VariableNames',"TypeofData");
    tempCoilNumberTable         =table(CoilNumber,'VariableNames',"CoilNumber");

    McadWindingPatternTable     =[tempPhaseNumberTable tempParallelPathNumberTable tempTypeofData tempCoilNumberTable ValueTable];
    MachineInfo=[Dimensions; Magnetics];
end