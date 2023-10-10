function extractedValues = extractNonNegative(array)
    % 배열에서 0 이상의 값을 추출
    extractedValues = array(array >= 0);
end