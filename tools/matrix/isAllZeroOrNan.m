function checkNZ=isAllZeroOrNan(A)
    % 배열 A의 모든 요소가 NaN 또는 0인지 확인
    if all(isnan(A(:)) | A(:) == 0)        
      checkNZ=1;
    else
      checkNZ=0;    
    end
end