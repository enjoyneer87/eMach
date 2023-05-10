path='Z:\01_Codes_Projects\Thesis_skku\Thesis_SKKU\figure'
filename='FundSVP.csv'
filepath=fullfile(path,filename)
svp=readtable(filepath)

tableVarNames=svp.Properties.VariableNames

% 변수 이름을 저장할 셀 배열 초기화
varNames = cell(size(tableVarNames));

% 각 변수 이름 처리
for i = 1:numel(tableVarNames)
    % 변수 이름 가져오기
    varName = tableVarNames{i};

    % 'x' 또는 'y' 제거
    if startsWith(varName, 'x')
        varName = varName(2:end);
    elseif startsWith(varName, 'y')
        varName = varName(2:end);
    end

    % 숫자 부분 추출
    numStr = regexp(varName, '\d+', 'match');
    if isempty(numStr)
        % 숫자 부분이 없으면 0으로 처리
        varNum = 0;
    else
        % 숫자 부분이 있으면 문자열을 숫자로 변환
        varNum = str2double(numStr{1});
    end

    % 변수 이름 저장
    varNames{i} = varNum;
end

%% Plot

svp1=svp(:,1:48)
svp1=table2array(svp1)
data=svp1;
for i = 1:24
quiver(data(1,(2*i)-1),data(1,2*i),data(2,2*i-1)-data(1,(2*i)-1),data(2,2*i)-data(1,2*i),1,'r','MaxHeadSize', 1,'LineWidth',2)
hold on
end

svp2=svp(:,51:98)
svp2=table2array(svp2)
data=svp2;
for i =1:24
quiver(data(1,(2*i)-1),data(1,2*i),data(2,2*i-1)-data(1,(2*i)-1),data(2,2*i)-data(1,2*i),1,'b','MaxHeadSize', 1,'LineWidth',2)
hold on
end

svp3=svp(:,101:148)
svp3=table2array(svp3)
data=svp3;
for i =1:24
quiver(data(1,(2*i)-1),data(1,2*i),data(2,2*i-1)-data(1,(2*i)-1),data(2,2*i)-data(1,2*i),1,'g','MaxHeadSize', 1,'LineWidth',2)
hold on
end
formatter_sci
%%

figure;
hold on;
start_pos = [0; 0];  % 시작 위치
for i = 1:24
    % 이전 위치에서 벡터값만큼 더한 위치 계산
    end_pos = start_pos + data(:, i);
    
    % quiver 그리기
    quiver(start_pos(1), start_pos(2), data(1, i), data(2, i),0.1);
    
    % 시작 위치 업데이트
    start_pos = end_pos;
end