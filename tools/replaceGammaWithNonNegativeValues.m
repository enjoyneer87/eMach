function inputTable = replaceGammaWithNonNegativeValues(inputTable)
    % 'Current Angle'에서 값 추출
    currentAngles = inputTable.('Current Angle');
    
    % 0 이상의 값만 추출
    extractedValues = extractNonNegative(currentAngles);
    uniqueAngle=unique(extractedValues);
    lengthPerEachAngle=length(currentAngles)/length(uniqueAngle);
    % 테이블의 'Current Angle' 값을 추출한 값으로 대체
    newCurrentAngleArray=[];
    for i=1:length(uniqueAngle)
    newCurrentAngleArray = [newCurrentAngleArray; ones(lengthPerEachAngle,1)*uniqueAngle(i)];
    end
    inputTable.('Current Angle')=newCurrentAngleArray;
    % updatedTable = inputTable(1:length(extractedValues), :); % 테이블의 행 수를 맞춤
end