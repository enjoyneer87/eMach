function [EMMapStruct,forceMapStruct] = sortMapdataPyleecanMat(EMMapStruct, forceMapStruct)

    %% EMmap Sorting
    % EMFileName에서 "case"와 ".mat" 사이의 숫자 추출
    for i = 1:length(EMMapStruct)
        EMFileName = EMMapStruct(i).EMFileName;
        expression = 'case(\d+)\.mat';
        match = regexp(EMFileName, expression, 'tokens');
        if ~isempty(match)
            caseNumber = str2double(match{1}{1});
            EMMapStruct(i).caseNumber = caseNumber;
        end
    end
    % sorting
    [~,index] = sortrows([EMMapStruct.caseNumber].'); 
    EMMapStruct = EMMapStruct(index);
    clear index
    %% Forcemap Sorting
    % forceFileName에서 "case"와 "force.mat" 사이의 숫자 추출
    for i = 1:length(forceMapStruct)
        forceFileName = forceMapStruct(i).forceFileName;
        expression = 'case(\d+)force\.mat';
        match = regexp(forceFileName, expression, 'tokens');
        if ~isempty(match)
            caseNumber = str2double(match{1}{1});
            forceMapStruct(i).caseNumber = caseNumber;
        end
    end
     % sorting
    [~,index] = sortrows([forceMapStruct.caseNumber].'); 
    forceMapStruct = forceMapStruct(index);
    clear index
end