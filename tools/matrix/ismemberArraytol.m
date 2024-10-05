function MVPTab_indices=ismemberArraytol(LongArray,ShortArray)

% LongArray=curMVPTab.PosX
% ShortArray=curDTNodes(:,1)
% 두 배열의 크기가 다를 경우, 허용 오차를 적용한 비교
tolerance = 0.000001;

% 허용 오차를 적용하여 두 배열의 모든 쌍에 대해 비교 (벡터화)
diffMatrix = abs(LongArray -ShortArray' ) <= tolerance;

% 일치하는 항목 찾기 (허용 오차 내에서 일치하는 값의 인덱스)
[MVPTab_indices, ~] = find(diffMatrix);

% % 일치하는 값 추출
% matchedValuesMVPTab = curMVPTab.PosX(MVPTab_indices);
% matchedValuesDTNodes = curDTNodes(DTNodes_indices, 1);

end