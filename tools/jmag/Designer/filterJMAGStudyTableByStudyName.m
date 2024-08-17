function filteredTable=filterJMAGStudyTableByStudyName(JMAGStudyTable,targetString)

% 'targetString'이 포함되어 있는지 검사하고자 하는 문자열
% targetString = '특정_문자열';

% 'StudyName' 셀 변수에서 'targetString'을 포함하는 행만 필터링
filteredRows = contains(JMAGStudyTable.StudyName, targetString);

% 필터링된 행으로 구성된 새로운 테이블 생성
filteredTable = JMAGStudyTable(filteredRows, :);

% 결과 출력

end