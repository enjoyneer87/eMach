%[text:tableOfContents]{"heading":"**목차**"}
% Z:\01_Codes_Projects\git_fork_emach\tools\motorCAD\optislang\Paretoplot.m

deepNetworkDesigner

%%
%[text] 레이어 라이브러리에서 featureInputLayer를 캔버스로 드래그합니다.
%[text] 레이어 라이브러리 필터를 사용하여 레이어를 찾을 수 있습니다. 
%[text] 레이어를 선택합니다. 속성 창에서 정규화를 "zscore"로 설정하고 입력 크기를 데이터의 피처 수로 설정합니다. 
%[text] 그런 다음, 완전히 연결된 레이어를 캔버스로 드래그합니다. 레이어를 연결하려면 featureInputLayer에서 일시 중지하고 out 포트를 클릭합니다. 화살표를 완전히 연결된 레이어의 in 포트로 드래그합니다. 
%[text] ![](text:image:353a)
%[text] Add a `layerNormalizationLayer` followed by a `reluLayer` to the canvas and connect them sequentially. 
%[text] ![](text:image:7ec4)
%[text] 
%[text] 숫자 피처의 데이터 세트(예: 공간 또는 시간 차원이 없는 표 형식 데이터)가 있는 경우 피처 입력 레이어를 사용하여 심층 신경망을 훈련할 수 있습니다.
%[text] 
%[text] 범주형 특징을 사용하여 네트워크를 훈련하려면 먼저 범주형 특징을 숫자로 변환해야 합니다. 먼저 모든 범주형 입력 변수의 이름이 포함된 문자열 배열을 지정하여 convertvars 함수를 사용하여 범주형 예측자를 범주로 변환합니다. 이 데이터 세트에는 "SensorCondition" 및 "ShaftCondition"이라는 이름의 범주형 특징이 두 개 있습니다.
%[text] 
%[text] 범주형 입력 변수를 반복합니다. 각 변수에 대해 원핫코드 함수를 사용하여 범주형 값을 원핫 인코딩된 벡터로 변환합니다.
%[text] 테이블의 처음 몇 행을 봅니다. 범주형 예측자가 여러 열로 분할되어 있음을 알 수 있습니다.
%[text] 
%[text] 
%%
%[text] %[text:anchor:H_6A039FBD] ## CSV Import
% sensitivityTable=readtable('Z:\Thesis\Optislang_Motorcad\HDEV_Code3\OPD\HDEV_ob2o24i28si1f1.py.opd\Samoo_HDEV_low_fidelity_sensitivity.csv');
sensitivityTable=readtable('D:\KangDH\Optislang_Motorcad\HDEV_CODE2\RESULT\Samoo_HDEV_low_fidelity_sensitivity.csv')
sensitivityTable = removevars(sensitivityTable, "x_");
varNames = sensitivityTable.Properties.VariableNames;
labelName2 = varNames{end-1}
labelName ='o_Weight_Act'
% labelName = 'o_Maxtorque'
tbl =sensitivityTable;
 
%%
%[text] %[text:anchor:H_A0B1CA84] ## feature
%[text] 범주형 특징을 사용하여 네트워크를 훈련하려면 먼저 범주형 특징을 숫자로 변환해야 합니다. 먼저 모든 범주형 입력 변수의 이름이 포함된 문자열 배열을 지정하여 convertvars 함수를 사용하여 범주형 예측자를 범주로 변환합니다. 이 데이터 세트에는 "SensorCondition" 및 "ShaftCondition"이라는 이름의 범주형 특징이 두 개 있습니다.
%[text] 범주형 입력 변수를 반복합니다. 각 변수에 대해 원핫코드 함수를 사용하여 범주형 값을 원핫 인코딩된 벡터로 변환합니다.
%[text] 테이블의 처음 몇 행을 봅니다. 범주형 예측자가 여러 열로 분할되어 있음을 알 수 있습니다.

%%
%[text] %[text:anchor:H_04649300] ## 2. 데이터셋 분할 (트레이닝, 검증)
%[text] 테스트용 데이터를 따로 분리합니다. 데이터를 85%의 데이터를 포함하는 학습 세트와 나머지 15%의 데이터를 포함하는 테스트 세트로 분할합니다. 데이터를 분할하려면 이 예제에 지원 파일로 첨부된 trainingPartitions 함수를 사용합니다. 이 파일에 액세스하려면 예제를 라이브 스크립트로 엽니다.
numObservations = size(tbl,1);
[idxTrain,idxTest] = trainingPartitions(numObservations,[0.85 0.15]);

tblTrain = tbl(idxTrain,:);
tblTest = tbl(idxTest,:);
%%
%[text] %[text:anchor:H_05E6923F] ## 3. 데이터를 트레인넷 함수가 지원하는 형식으로 변환합니다. 
%[text] 예측자(predictors)와 대상(targets)을 각각 숫자 배열과 범주 배열로 변환합니다. 
%[text] 특징 입력(feature)의 경우, 네트워크는 관측값에 해당하는 행과 특징에 해당하는 열이 있는 데이터를 기대합니다. 데이터의 레이아웃이 다른 경우 이 레이아웃을 갖도록 데이터를 전처리하거나 데이터 형식을 사용하여 레이아웃 정보를 제공할 수 있습니다. 자세한 내용은[ 딥 러닝 데이터 형식](https://www.mathworks.com/help/releases/R2024a/deeplearning/ug/deep-learning-data-formats.html)을 참조하세요
predictorNamesCell = varNames(1:30); %[text:anchor:H_50508A30]
predictorNames = string(predictorNamesCell);
responseName = labelName;

XTrain = table2array(tblTrain(:,predictorNames));
TTrain = tblTrain.(labelName);
TTrain2 = tblTrain.(labelName2);

XTest = table2array(tblTest(:,predictorNames));
TTest = tblTest.(labelName);
TTest2 = tblTest.(labelName2);

% 입력 및 출력 데이터 추출
XTrain = tblTrain{:, predictorNames};
% YTrain = tblTrain{:, labelName};
YTrain2 = tblTrain{:, labelName2};

XTest = tblTest{:, predictorNames};
% YTest = tblTest{:, labelName};
YTest2 = tblTest{:, labelName2};
%[text] %[text:anchor:H_C3889592] ## 딥러닝 데이터 형식
%[text] 대부분의 딥러닝 네트워크와 함수는 서로 다른 방식으로 입력 데이터의 여러 차원에서 작동합니다.
%[text] 예를 들어, LSTM 연산은 입력 데이터의 시간 차원을 반복하고, 배치 정규화 연산은 입력 데이터의 배치 차원을 정규화합니다.
%[text] 데이터에는 여러 가지 유형의 레이아웃이 있을 수 있습니다.
%[text] - 데이터는 여러 차원을 가질 수 있습니다. 예를 들어, 이미지와 비디오 데이터를 각각 4차원과 5차원 배열로 표현할 수 있습니다.
%[text] - 데이터의 차원은 여러 가지를 나타낼 수 있습니다. 예를 들어, 이미지 데이터는 두 개의 공간 차원, 하나의 채널 차원, 하나의 배치 차원을 갖습니다.
%[text] - 데이터는 여러 순열의 차원을 가질 수 있습니다. 예를 들어, 시퀀스 배치는 채널, 시간 단계 및 관찰에 해당하는 차원을 가진 3차원 배열로 표현될 수 있습니다. 이러한 차원은 어떤 순서로든 될 수 있습니다. \
%[text] 소프트웨어가 올바른 차원에서 작동하는지 확인하려면 다양한 방법으로 데이터 레이아웃 정보를 제공할 수 있습니다.
%[text] 
%[text] *레이블이 지정된 차원을 입력 데이터에 제공하거나, 추가 레이아웃 정보를 입력 데이터에 제공하려면 데이터 형식을* 사용할 수 있습니다 .
%[text] 데이터 형식은 문자열이며, 각 문자는 해당 데이터 차원의 유형을 설명합니다.
%[text] 문자는 다음과 같습니다.
%[text] - `"S"`— 공간
%[text] - `"C"`— 채널
%[text] - `"B"`— 배치
%[text] - `"T"`- 시간
%[text] - `"U"`— 미지정 \
%[text] `"CBT"`예를 들어, 첫 번째, 두 번째, 세 번째 차원이 각각 채널, 관찰 및 시간 단계에 해당하는 시퀀스 배치를 포함하는 배열을 고려합니다. 이 배열이 (채널, 배치, 시간) 형식을 갖도록 지정할 수 있습니다.
%[text] %[text:anchor:H_18D4BA89] ## 4. Feature Input Layer 
%[text] %[text:anchor:H_628D8347] #### 라벨 -  GearToothCondition
%[text] 특징 입력 계층( a feature input layer )으로 네트워크를 정의하고 특징의 수(the number of features)를 지정합니다. - 현재는 category형
%[text] 또한 Z-점수 정규화를 사용하여 데이터를 정규화하도록 입력 계층을 구성합니다.
numFeatures = size(XTrain,2);
% numClasses = numel(classNames);
% 모델 아키텍처 정의
% layers = [
%     featureInputLayer(numFeatures)
%     fullyConnectedLayer(64)
%     reluLayer
%     fullyConnectedLayer(32)
%     reluLayer
%     fullyConnectedLayer(1)
%     regressionLayer];
layers = [
    featureInputLayer(numFeatures)
    fullyConnectedLayer(64)
    reluLayer
    fullyConnectedLayer(32)
    reluLayer
    fullyConnectedLayer(1)
    ];
%[text] %[text:anchor:H_B28B45BA] ## 훈련 옵션을 지정합니다:
%[text] - L-BFGS 솔버를 사용해 훈련합니다. 이 솔버는 네트워크가 작고 데이터가 메모리에 맞는 작업에 적합합니다.  -\> adam
%[text] - CPU를 사용하여 훈련. 네트워크와 데이터가 작기 때문에 CPU가 더 적합합니다. \
%[text]                 \-\> GPU
%[text] - 훈련 진행 상황을 플롯으로 표시합니다.
%[text] - 자세한 출력을 억제합니다.
%[text] -  \
% 학습 옵션 설정
options = trainingOptions('adam', ...
    'MaxEpochs', 200, ...
    'MiniBatchSize', 32, ...
    'InitialLearnRate', 1e-3, ...
    'Verbose', true, ...
    'Plots', 'training-progress', ...
    'Shuffle', 'every-epoch');

%%
%[text] %[text:anchor:H_5FEE9003] ## 5. 트레인넷 함수를 사용해 네트워크를 훈련합니다. 
%[text] 분류를 위해 교차 엔트로피 손실을 사용합니다.
%[text] %[text:anchor:H_9F98E037] ## -\>TraninNetwork Option \> Loss Function
%[text] [https://kr.mathworks.com/help/releases/R2024a/deeplearning/ref/trainnet.html](https://kr.mathworks.com/help/releases/R2024a/deeplearning/ref/trainnet.html)
%[text] - `"mse"`
%[text] - `"mean-squared-error"`
%[text] - `"l2loss"`
%[text] - `"mae"`
%[text] - `"mean-absolute-error"`
%[text] - `"l1loss"`
%[text] - `"huber"` \
% net = trainnet(XTrain,TTrain,layers,"mean-squared-error",options);
% net = trainNetwork(XTrain, YTrain, layers ,options);
% net = trainnet(XTrain,YTrain,layers,"mean-squared-error",options);
net2 = trainnet(XTrain,YTrain2,layers,"mean-squared-error",options);


net.plot
net.layerGraph
net.activations(XTrain,1)
%[text] %[text:anchor:H_61F53EA9] ## 
%%
%[text] %[text:anchor:H_E1E42B34] ## GT - Prediction

% 예측값 계산
YPred = predict(net, XTest);
YPred2 = predict(net2, XTest);

YPred2 = predict(net, XTest);


% 실제값과 예측값 비교 그래프
figure;
plot(YTest, 'b-o'); hold on;
plot(YPred, 'r-*');
legend('Ground Truth', 'Prediction');
xlabel('Sample Index');
ylabel('Value');
title('Ground Truth vs Prediction');
grid on;

scatter(YTrain,YPred)
hold on
scatter(YTest,YPred2,'red')

scatter(YPred,YPred2,'red')
hold on
scatter(YTrain,YTrain2,'blue')


%[appendix]{"version":"1.0"}
%---
%[metadata:view]
%   data: {"layout":"inline","rightPanelPercent":40}
%---
%[text:image:353a]
%   data: {"align":"baseline","height":147,"src":"data:image\/png;base64,iVBORw0KGgoAAAANSUhEUgAAAM0AAACTCAYAAAAtOJ3uAAATjklEQVR4Ae2d\/Y8dVRnH\/ReMMcbEH7btpWzfabuFFmgLxdryIiR0BRJFuoJLIyAQ4wukC3W3BgSMxFy3rmiqZFkJRXajUGxpKUnNrtU0IeUHKSHbbEywvxisdjEt2sd5zsyZeebcmXPn3Du3e2fud5LJnTtz5swzz\/l+zvOcM3d3PkFY4AF4wMkDn3AqjcLwADxAgAYigAccPQBoHB2G4vBAKaE5ceIE7d27l4aGhmjXrl1Y4YNEDbA+WCesF5eldNAcOHCARkZG6O2336YzZ87Q7OwsVvggUQOsD9YJ64V1k3UpFTTcY7ADAAs6CpfOkvXCuskacUoFDYda7jlcHIayAIw1wLph\/WRZSgUN56iIMoCgkY6QdcP6ybKUChoe9DfiMJwD0FgDrJ8sS0dA88mH36S5WAFjsWAENGLGaC6A4WsCGkCTJXLNaZm09KxtoTk6SJVKxVv7aHS6\/QQ2OeTZNjTZMfAj0qREmu7ubsp7TYPSHmlmaHR7hfrGZpoU5SQNeuANHs0futZD0zrb7b5P9hWgSYGmq6uL9u3bl9u6aNGi1PGSveF8aJoXe3sJz37Ppljby3ZAY4HmyJEjlMfK8DUKDUcZPzWLUqCZsb5o3\/ZRmhH3MBumcv55foTywdP1KABVuUGa1OdOj1KfTv\/U9iANctolopOKKCpNjGxh8UeRJoiKQ4NeXf65lUp0Db\/cqIqcvi3RMd9u8T20J8F2bfMcfQIa4XiZPnGkyQMYrqMZaGZnAyHq9MwQeyRY7p25R+6Lxj2xskZvHTvmnRuKVG\/HU0IFagho3KbIBi1wLf7gezDeUeVMCHWdNnvUfbUmtXSLeH4EBDQWaPbs2UN5rPwwrNFIY0LDwouNb4KoEEYMcT9+RNICdoVGwBeAG0sRWeSB4E1opH3RsSAiaUjYTgkqoJnTybG6F+eeIqmHkZFm6dKltG3btrrrAw88QL29vXXLrVq1qqkxTVKapdOtaFZN9\/RBarad07g8oPGBi64XT70iMPzrW6GJzbKJyAho6up2TgtkgYbTsyzLyZMn6cKFC3WLcn0SSrmdBHC0Ly7EmkgjIkvNuCAmxJwjjbiuEzSINHW10pYFigyNCUYsBVOQ6LRKR52USKNSo2ic4NcTnCvTpgCO+Jgmnmo5QSPGXOo8DZHNHoxp5p6jQkPjidgXuE6RNCQ8SNWg8DFv\/1ExI+adp0RaicZE+junXX1jo9EkQgI0HPlk+SjtC\/artMu\/vj0982blvOvVzJ4Z9cfsEcdk3VE09gfoF+s76yfL0nG\/PWuf9OziCqKVwlPQxcY0xbw3QOP1YloocpwBaCK\/aP80+wlossSnNi2TNT3jQX4zK4MnVwml3G5WjEU5H9C0KRBZzMoKTZa6bLNnDIx+QMrbEhS5XRTRw04\/+iI9a2F6BmjyT\/HaAVxAUwBopob7qb\/fW3dO0LSwN7OATk3QQH+Vpho5N+UctmlgfDocD2a2JaW+2Pkxe6eo6t17dap9AAQ0ohFlysRRIsvS+vRsmiZ2DtDEqSZEExNhE\/UIXwGa+urAlHOKj957773UXwTkkZ5N7AyiTNjbMkTmvgCEqaofkTgqheX9nlpFKo42JkB8jo5ganvAi0oiqsk6dTkPnhg06rwqVUO7NOS+rdVxjnS+TWF0SrXDsHfWHmmmxwfEPQfXNetWdUSRNozcnk1xe7x7V\/cQlY1FwKDTQKQRvacZaVj0za5yIkDX9bmerbFJgaSGifYFwgvSE9Xgw1N+WqQELYWixTpLSkxa5FJEcpvvXQk+SPtkfXxMldV1BrAG166BJoRUlgu2dWoo67PZETtmgUbZGwk88k3cZ+oeA7tr\/RKkfuqa2dJAQJMCjQTIZftT975EC5f3qF9Ha2D0J\/9iurKsJwYM1x0BkpQ6SQGYApLHjHMlDFKEcjsRmkiEMYEZZWuhMc5TIvXtC3tzr47wPJsdsWPmPRv3KdpP2Svg0Nfla\/pjonr26A4i\/RrcVoBGON0FDltZBmfRih71dzQaGP6bGo40n75zuGlo\/FQrStGkOGLHGok0+hzPL0qEQVoV1evDEYqf\/ScB1ecJaOQgPjwvBoZRR+yYDRofgsg2zycBNCpKqnvh8zXQCeX5\/vic2DUBTc1ohHuKpN7dBoLrscrND9L667aShmbT5q302esfrAGG602yJdrnN7QvPBZASm9opCoxIUtByG0tcA1KqvhrRRSKPwM0GurZWdHT2+yIHUuHxoyEMtL41\/J8Ne6N2TRIwfUlxKGfY9esvd+wnHe\/iDTc6MHqCoatPEeb+VdspYceekitl66Lj2Pkufr6yZ8SGj+9CUWgGjpIPWLQBD2qhkEKQp4TiCg+ESCmtVXZCFIGRZd1gUafExsj2eyQ9lomAuLQ+HCFvvHaVEdKCUnSOQrq2DUjTSS1CaBpETQMhR7fcFrG2xIUuZ3UMNG+ODS6t9YpidmL+\/s9oU\/JZzOBoII0RYupn6MW98QaLiPSKBsUjDoV1GmOGJuw\/4zzVP0yPRuOZvVqBKzSP8OOAJR+Za+2Xdvgf0aRV+\/3bDPsSEu5FPw67dRRCNDUZGSxHRcjPdNQfObWwcRxjD7OnxEg9h6ueOVM4C\/u\/UXw5ntdRJoWRhoJhm27eDBkFeHcQeNHkygy5uljQANoShzpssLtVg7QABpAIzSQJSIBGkeHZXEqyrj13EXzV0dCg5c6lVvUrYSwY1\/qhNcHAppGwerY1wfiRbWAphFoOvpFtfzQBq9EBzhZwWFYOv6V6PpJJ0ccTtV4jMODO6zwQZIGWB+sk6yvQtf6KtUfoembwmeyB8bGxpIPYK+TBwCNk7uKXRjQ5NN+gCYfPxaiFkCTTzMBmnz8WIhaAE0+zQRo8vFjIWo5fPhwIexsdyMBTbu3UI72IdLk40xAk48fC1ELoMmnmQBNPn4sRC2AJp9mAjT5+LEQtQCafJoJ0OTjx0LUAmjyaSZAk48f276W8+fPq\/\/X1vaGFsBAQFOARsrDxNOnT9PBgwfzqKrj6wA0HSKB48eP0zvvvNMhd9va2wQ0rfVvW9T+0Ucf0Ysvvkhnz55tC3uKbgSgKXoLZrB\/cnJS\/d1IhqIoksEDgCaDk4pchFOyQ4cOFfkW2s52QNN2TZKfQQzM\/v371b9yyq9W1ARoSqgBHsNwSsYRhv\/0F0u+HgA0+fpzzmrj5zA8rcyzZDzo5799x9IaDwCanPzKM1OcDvGzEH7RE2\/zE\/iLtfI1+dp8XcyS5dSoKdUAmhTHuOzmXp17d+7lubfnXh9LeT0AaJpoWx4v8LiBxw88jsDSGR4ANA22MwPDM1OcDmHpLA8AmgbbmyMMgGnQeQU\/DdA00IA8huGUDEtnegDQOLY7z0zxoB9jGEfHlag4oHFsTE7JeJYMS+d6ANA4tj0\/C+FpZSyd6wFA49j2\/BARz2EcnVay4oDGsUExY+bosBIWBzSOjYp\/TuHosBIWBzSOjQpoHB1WwuKAxrFRAY2jw0pYHNA4NiqgcXRYCYsDGsdGBTSODithcUDj2KiAxtFhJSwOaBwbFdA4OqyExQGNY6MCGkeHlbA4oHFsVEDj6LASFgc0jo0KaBwdVsLigMaxUQGNo8NKWBzQODYqoHF0WAmLAxrHRgU0jg4rYXFA49iogMbRYSUsDmgcGxXQODqshMUBjWOjAhpHh5WwOKBxbNTDhw87noHiZfMAoHFsUUQaR4eVsDigcWxUQOPosBIWBzSOjQpoHB1WwuKAxtKo\/E80zPWVV16p2WepAodK6AFAU6dR+Z+cc3RJWvnfOX388cd1asDhsnkA0NRp0Q8++CARGIYI\/86pjvNKehjQZGjYY8eO1YCDKJPBcSUtAmgyNOy5c+fo5ZdfjoGDKJPBcSUtAmgyNuz7778fQoMok9FpJS0GaBwa9siRIwocRBkHp5WwKKBxaNQPP\/xQvbkZM2YOTith0VRoTpw4QXv37qWhoSHatWsXVvggUQOsD9YJ66VTlkRoDhw4QCMjI8SvyTtz5gzxS1mxwgdJGmB9sE5YL6ybTlhqoOEegx0AWABJEiRp+1gvrJtOiDg10HCo5Z4jzTnYD5jSNMC6Yf2UfamBhnNURBmAkQaGbT\/rhvVT9qUGGh702xyDYwDKpgHWT9mXzNBceOsmmovV1kA41n4AAxoxazYXwPA1AUb7gWFrE0BTBGiODlKlUvHWPhqdLpbAbOIr6jFAY4Hmr6Ofp97r11BXV5f65O+tiEZ28czQ6PYK9Y3NICKJtrL7rLUdC6ARDWECwcA8\/\/zzaszHn\/zdLJPHd7sAfGgGj7ZWCHYbcG3pH0BjgYYjjFz4+8kX8o82skHMbY4yfmrmfQ5NqmgzM9YX7ds+SjPiHszz8T1\/4AGNEJwZNWSk2b17N82fP49WL6\/QVasvoW995TLat\/tq+ttvtzQdfezCNtIzNb4ZpMnA7smhCCZ7PfmLp1OvB2gs0JhjmvEnrqYVSxbQz767lkYfv5Luv30F9XgQbb6qmx67ZzW9+vR6+serW2MQmXUkjYvs4otDA0jmHn5AY4HGjDz8\/S\/PbaLlixcQA6SPn\/jVdTTigfS1W5bR4kvn0y2bFtET3+ihN3+ykW7d2lN3XJQdmjhA9vPmXlxltQ\/QOELDoPz5uWtp2aL5NPFkBI4GiD\/\/NLKJnn34cg+exWrmzRwXybK8bRdXHBREmrnvDABNA9Cw0I\/9fBMt6Z5Pv\/vh+jDi8P7\/vHEj\/eb7V9IdW5fQ2pWX0OLuSo6RxhOMMaZRkwKYDKjT8eQLGqBpEBoGhCPKku4F9Pun1tPUyLX0vbtWUvfC+bSjdzm9\/qMNNHD3avrSliV1n\/W4RBouG5s9q0STAvZ68hVOJ18L0FigqTeI\/\/v4FnqkbxXNm9elZtT2fGct8T4G6rG7V9H2m5fR\/47U\/z1bJwuwiPcOaCzQyCln+XCTowhHE44qHF1+8eg6tf3aM36q9vg9q+iuLy6l\/755Yyx1Y5iS1iIKp5NtBjQWaJIebi72xjE8O8bjFh6\/aAj+OHwNLazMUzNod960lM4fjo7pMmmfnSzAIt47oLFAY0aaa9Yto0e3r6LLli6gb95xmZpFkyDs6F2hUrXXntkQwiSPp20XUTidbDOgsUCTNqY5d+hGeu6RtbTx8oX0VS+qvPHsRhq6t4e+fMNS9WymsqCLDv54Y2ZwOlmARbx3QGOBJi0yyP38U5o1Kyq0dNECL2W7SoHyVvUaWuD95IZhkmXTtusJZ2q4n\/r7vXXnBE0Le2PnnZqggf4qTfHxqaq9bFjHFFW5Xr3a6g\/PuYizcPKeHK4\/PT6Q8f4buxdAIxojTdS2\/T\/Y0aOeybz29AYVdTj6cBQ65AHDv1X79cC6Jqecp2li5wBNnKrTwFJgmaDxgRkYnw6fcbRabDHIhd9T98t7ylI+KNPq+wA0ojFscCQd45\/K3O49hzl74IYwovCvBXi8w79Ru\/+2FbR29eKmHm5O7IwiQXWKAeqn6pQGiIUfACUFpqHRn\/oeuUwQTZKFZdSv6tTXD6IY16XqrVI1tE1DHZw\/7EU6Hb2Gp0IoZ9Pq4zrlMWWjjILBtWUZHVX1vbFN6poDVB1GpJG\/QmlkuyX\/I+DJ+3roti2L6d9\/iICRYL3r\/cHa129dnsPPaKSQ5TaDUwcaedwTF4PiRxa\/Hhllanv7eCRSKaJO3wKB+vD6dfUrOILtWDkNlF+fBj5Wn2EnH1O2KUg0rJbzA5hi9mgbNFQ5fiLSCGdK0du2n7p\/DfVuXkz\/ej0OzPFfbqKffvsK4ilnngzo3byE1jUZaWZnJShyOws0s8QCjMSkBWzWw3UZa0yw3jH1PThfQaPF7MMooYlgFFAb5\/j1BXXwsSSRSxtczk+rz7zHBr8DGuE4E5Sk2bOnH2BgltA\/919P776wmfbuvFI96OR07IYN3TTYv1rNnGmgkuowr1MjWGFTs9CoVIqjAAswFKYPTSRuAxi+vilSGQ0MUapUT0QaHU1ikVDVp1M9\/elDmJwqalAFWDrlCz9Tzjfss\/s34d5j\/q89DmiEg0wxm89p1qzsVtPM9\/FYZWVFbfMvAvjPBE5PxP+OxqzL9t3eqDIqyG0tqqD3N3vlEBDu7as0EaZmvgjShBpGJlkf+0h9F5EmrL820qRCI86J3XOayKUNaWU04LJuW1nR3jEbHPYDGuEsU9hJvwjYsW05jXlTy6de+kI4+DfPc\/1ubzwJir\/tp0KBWG0TAcG9qfGDLhferz9GkNFGgRQOsOPHVR1amIYoM0UaFal0qqhtD6KIBNKzT11LR0fDHg1kkq1RGupFMm1reL+1EcPu9\/TygEY41RS7GWn4u1kmj+\/2xpPQ6B7fT28Gxifss2f63gyRR9fzwQhnukKBBoJRYtapVDSGMZ8DZYMmbnu\/CTHbqNOuUPDaPgmXtieIevIeg\/Ornl\/CVFRGKy7L11GppH+PDKjsOCLfBD7Q9YtPQCOcYQKQZTxintPI9ywN1UyZRoTRzPXKfi6gsUDTCACNnNM6kQXpXNhzp\/eerbOhfNcENKWGpnyCbQe4AQ2gqX1GI3zSDiJtNxsADQQCaBw10JHQ4KVOSNsajV4d+1InvD4Q0DQKTce+PhAvqgU0jUDT0S+q5Z9K45XoACcrOAxLx78SXf99AUccTtV4jMODO6zwQZIGWB+sk054Fbpmo+bvafQBfMID8ECyB\/4P+aJGblo8pfYAAAAASUVORK5CYII=","width":205}
%---
%[text:image:7ec4]
%   data: {"align":"baseline","height":318,"src":"data:image\/png;base64,iVBORw0KGgoAAAANSUhEUgAAAMEAAAE+CAYAAAA08XTkAAAkx0lEQVR4Ae2d\/Y8d1XnH8y9UUVVV6g+LuRDbGAzGBEwCJKSuyUuTKBhC1NJ4G7qgBppEDaVBXuLuUpKGVEXNrekSKodo2RrsejclMbVjx0i29uIgR5GdqHFkrbNCMpaSxnXxujGmfjrPmXNmzjl3Zu68v9z5jjS683Le5jnfz3meM3PvnXcQFlig5RZ4R8uvH5cPC1CjITh69Cht27aNJicnacuWLVhhg0ANsD5YJ6yXoKWxEOzZs4empqboxz\/+MZ09e5aWlpawwgaBGmB9sE5YL6wbe2kkBEw0XxDED\/CTDH6sF9aN7REaCQG7NiY7iQGQFsCwBlg3rB99aSQEHOPBC0DUaQY21g3rR18aCQFPgtMYAHkADmuA9aMvQwXBb33hB1TFCriaBRcgKAAUQAAIdM9SynZYOFSFF+A6B0JwcII6nY6zjtL0Qv0EMz\/ptG1yfvB1DMkt2NZ4guXLl1Peaxhk0RAs0vSmDo3OLGYU2TxNOCBNHMwfouIhKK7t0bYPtlVrIBgZGaEdO3bktq5YsSJ0vhHdES4E2cVbLyFFX7Mtvnq1vVUQHDhwgPJYGaa0ELAXcEMhP+RYnBn1j22apkU9zPBCJzef60FckFQ5AiiRboLmVd6FaRpV4ZbYnqAJDnM07yFGfBGW+W1hMfueQHqtyQmnLDdvp+PX4aabFp7NbYt\/bim0PQFtV22u6BMQpAAjCwRLS1JYKhyyxOILkEdPHjFH\/XmDkdYaTY1zTt4+CMwQTIDnAWe2yW+DEqwSt9yX8wWRzoZKlRnVHnFdxYRyyTyS66FaBcHTTz9Neaz8cCWtJ7AhYCEZ8wM5ansjujY6uh5DCTIpBBpMEkQjJGPRSgHbEOjt889Jj6FEz+3UwQMEpdwU8iphkoNGAH3iumrVKrrzzjsHrg899BBt3LhxYLo1a9ZkmhMEhTUqvPHvGqmRWIZCmzhsygMCFyC\/PjPU8YXu1h8JgXEXSfNcgMDTZykbcSDgiXGc5fjx43Tp0qWBSbk8HTJ9OwhI\/5gprD5PoI38fXG1IaycPYFWbyII4AkGaqWUBE2GwBa6EfII0aswRnmFEE8gQhE\/znbLkXn1MEWK3ZwTmKFNIgi0OYvIp6CIag\/mBPlz0WgIHFG6glUhiRI9T9qU8Pmcc\/ygdsfHySdE1\/HnFGqfw5zRmWl\/Uh0AAXsmPb0fZsnjIsxx648Oh5y7Tk59fXeHrPKN9mjn9LJ9b+lOWMvaZ\/3oy9B+d6g+4VC5HVykkARExpygmdcGCPQhwNkufk7QTKEEwQQILPFUuRs3HGKBZ1nZm+irPhnWt4MEM4zHAEGVqrfqjguBlS1wN8oTMADqiTNv68LXt4dR8MN8TQiHLBQAwfCEa3HBBQQVQNDbOkZjY866eY4WnDslcTvLS3dyjsbHutRLkzckD7dpfHYheVtCyvPayueN9vao61x7t5fiuuPUlSINICgdggWa2zxOcycziMAQVYZyNMEAAl8Irb9F+vOf\/zz0iXEec4K5zdILeKMhQ2Efk8LudV2PwV7DS++OpMKTsDewgeA8ysOI7XHHa2heRy9TpXNgMCAQ+brU9dqloHXb2p1lT+S2yfMeoe2w2rsU7QkWZse1a5b12mWLMnxP6HlWp01me5xrF9fgpzU8lBwEWuUJ9Ds7abf1ibEq4\/fW3mFMkoMM7R+TQpLhgOjArT03DBEC1TteiW+JhDiUaHVR6NvcqULAMszSy+NzIq0qU8In6+6DwINOTye3VSimlxfVDuNcBASivb5gfduYNhPXKNvdbxcZaok644VdrYFAv3uTZPud979IV16zVnz7VAGgPvkbqZ2r1xoAcNm+4INCFb1DbUHo56y8urh1UenbgRD4ojIEY6Xth8DKJ0Tnts8bbZ0yvHxR7TDO2ddsXSe3S66ivZrYVb1cpzunGNQeBbxfpipb\/wQEMX5ozyCsWL1W\/CpNAcC\/KWBP8Nv3bs0MgRva+CGR3tnGuTSeQOVxhCVEJcMYv1xX7J6YWYA6cCqfBoE+qfXyGUK3yjDORUHgitpvm2MTCYHwYuJaOL8CNCA9Xx\/nMeoEBH0iTeIJVNrORz9Ht3zgDlIQ3L7+DvrdD34usGx9lOnfdjvOFRJ3aMhoZYUGhjD1Dta3lWCV8EPF3C8KT8wxIFCQLi1pI3FUO4xz4RDYnkr3BG5djq1mnTmPAkPWr0Pp2duos\/96vXTO9cITxPAEDAJ7g2U33kGf\/\/znxfqudeY8QMHCn7qB+7d1CNxwwutU0XHS1RsQyBFPiVvvYD2PFIU5MdZuw4q0PnQsfJU2CQQqjzHHiGqH3t6IibEJgQuLZxsFuDdXcYUdlEdAatQJCAJHa120cbfV\/IDDIN4Oy9cvfL0TTAjUaKpCAHuUdY87wu3pzwakQGRYIIQgwhw5UipYLE8g2iXgUqGXCiu02D6GJ+hu9e9a6aNwaDuk8MdEe1XbVRvcT98zquNO2+z2hwhbwKzCPOUlQtIG9Q08QUxPoAT\/O5+YCJwHqPP8GWTo4ThmA6zDXfy2gEyJnGHNaQUECSHQxR62nVfn1K+c6iBwR3vfc+VpG0AACHIbUfMUZpllAQJAAAiG+ZdlZY4mqCu\/GL1sWw6FJ8BLOporwLIFb9c3NC\/pwOuaAIEt7rj7Q\/O6Jry4DxDEFb2ebqhe3MffBMcrXAGCLvCobRb\/0L3CVf0cgj0Ch0Y8R+DJDlbYIEgDrA\/Wif3qVqWjRv6oRjUen8EWmJmZCT6Bo4EWAASBZmn2QUCQrP8AQTJ7NSI1IEjWTYAgmb0akRoQJOsmQJDMXo1IvX\/\/\/ka0sy6NBAR16Ykc2wFPkMyYgCCZvRqRGhAk6yZAkMxejUgNCJJ1EyBIZq9GpAYEyboJECSzVyNSA4Jk3QQIktmr9qnfeust8X9JtW9ojRoICGrUGXk05fTp07R37948impNGYBgyLr6yJEjdOzYsSG7qmIvBxAUa99SSz9\/\/jxt376dzp07V2q9Ta8MEDS9B7X2z8\/Pi+\/Na4ewGcMCgCCGkZqQhEOgffv2NaGptWsjIKhdlyRvEAOwe\/du8VcqyXMjByBosAZ4DsAhEHsA\/nkhlnQWAATp7FZZLn4OwLdB+S4QT4L5t7NYslkAEGSzn8jNd2M4JOH78\/wyD97mp7ZFrFw+18N14C5QDp3nFAEIMtqRR2IekXlk5hGaR2oszbIAIEjZXxyDcyzOMTnH5liaawFAkKLvGAC+G8MhCZbmWwAQpOhD9gAAIIXhapoFECTsGJ4DcAiEZXgsAAgS9CXfjeFJMOYACYzWgKSAIEEncQjEd4GwDJcFAEGC\/uT783wbFMtwWQAQJOhPflCF5wAJDNaQpIAgQUfhjlACYzUoKSBI0Fn4AXsCYzUoKSBI0FmAIIGxGpQUECToLECQwFgNSgoIEnQWIEhgrAYlBQQJOgsQJDBWg5ICggSdBQgSGKtBSQFBgs4CBAmM1aCkgCBBZwGCBMZqUFJAkKCz8AaYBMZqUFJAkKCz4AkSGKtBSQFBgs4CBAmM1aCkgCBBZwGCBMZqUFJAENJZ\/GU5e921a1ffsZDsONwgCwCCiM7iH9Pz6B+08teqL168GJEbp5piAUAQ0VOnTp0KBIChwNeqIwzXsFOAYECHHT58uA8EeIEBRmvYaUAwoMMuXLhAO3fuNECAFxhgtIadBgQxOuzEiRMeBPACMQzWsCSAIGaHHThwQIAALxDTYA1KBghidtaZM2fEP07jjlBMgzUoWSAER48epW3bttHk5CRt2bIFK2wQqAHWB+uE9dLkpQ+CPXv20NTUlHj5w9mzZ8UbUPgPaLHCBrYGWB\/8t5SsF9ZNUxcDAiaaLwjih+BtwUfts15YN031CAYE7NqY7KgLxjkAEqQB1g3rp4mLAQHHePACEHmQyAcdY92wfpq4GBDwJHjQxeI8IAnTAOuniUssCC698hGqYg0zNo7XE0RAUAAoEHs9xR7WL4CgCggOTlCn03HWUZpeaJZgwoTU5OOtguA\/p3+fNn7wBhoZGRGfvF9EuBQtiEWa3tSh0ZlFzGNq8hynVRAwAN\/+9rfFHIg\/eb8qCCYOwgNEDxbl2adVELAH0BfeP\/58\/t4gqnPZC7ihkPM5OS+8weLMqH9s0zQt1mSEjLqOYTrXKgh0T\/D444\/TsmWX0fXXdOg9119Bf\/nH19KOx99Lr\/\/bhszeIVogVjgk5gcTNC+FPz\/pwxFdTnkj5bC3o1UQ2HOC2a+8l1ZfdTn98yM30fSXb6YHP7ma1jpQrH\/Pcnrsvuvpu0\/eQv\/13TsMKOwyguYV0aIxIYDoq4e5VRAExf+vffN2umbl5cRAqPNHv\/UBmnLA+NOPXU0r37WMPnb7CvrKn6+lH\/zjbfSJO9YOnFfEh8AEIjpf9WIZ1va1HgIW\/g+\/+X66esUymvuqD4ICgj9fnbqdnvrCux0YVoo7S\/a8Qk\/L29FiMYUPT1A93IBAPic4\/MztdNXyZfTvf3eL5xFY0P\/7\/Q\/Tv\/7NzXTPHVfRTdddQSuXd3L0BI4ArDmBmCRjcjxgIMkXHEAgIVAj\/lXLL6eXvnYL9abeT3\/96eto+ZXL6IGN19DLf38rjX\/merprw1UDnzUk8QSc1rg71PEnydHl5CuENtfVKggGTWrfmN1AXxpdQ5ddNiLuGD39VzcRH2NAHvvMGtr00avp\/w4M\/j5SmwXVxGtvFQT6LVL9YRmP8jza86jPo\/+zj64T29\/7uhsaffm+NfTpP1xFb\/\/gw0aoxHAErU0UQpvb3CoIgh6WrXTmAXz3h+N+jv+VqA9tfR9d2blM3CG69yOr6K39\/jmVJuyzzYJq4rW3CgLbE7xv3dX06KY1dO2qy+kv7rlW3CXShf3AxtUiNPre12\/14NDPh203UQhtbnOrIAibE1zY92H65pduotvefSX9iTPqf\/+p22jy\/rX0Rx9aJZ4NdC4fob3\/cFtsENosqCZee6sgCBu59eP81YkbVndo1YrLnRDpPUL4r3TfR5c7X7FgOPS0YduDhNDbOkZjY866eY4Wwr4ndHKOxse61OPzvW50Wq+MHnW5XLVGle\/lKfEuk35NCepfmB2Pef3prgUQWJPbv31grXgm8L0nbxVegb0De4l9DgD8XaPnxtdlvEW6QHObx2nu5IAO0wUTCwIXgPHZBe8ee9HiGQR733n9mgCB\/sw11XYhP6\/kr0Z80nkOcG7Ph7wRn58m83yBv2P04N2r6abrV2Z6WDa32R+puz0GYoy6PQUEC1kCogtGQaA+lYA4jRztgwVvlS\/KVPVLL8NliXK71PXapiCV+bc6nkh5l609D7KlsPK4TP2caKPupWTdehrl9dS1cZtEnePU3QpPEERJ7hB89bNr6e4NK+nN\/\/AB0MOdnzk\/wPmzT1yTw9cmdGHq2wzCAAj0845YWPjuyO+Wo3uBvlFY5B2T6ZdIhGQqXJKCc2F0yxoTYpfbRjoFiCtqBbBRntVOPifaJkSv4IvIL+Ew2qPaoCDJ8RPhkBMOfe3BG2jj+pX0Py+bABz5l9vpnx6+kfgWKU+ON66\/itZl9ARLS7rw9e04ELji9cWhBGmXw2VZqyFA55zYl\/kFBEqcLlw6BD5cGqRWHrc8WQafCxKt3oYk+cPKs68x5X6rIAi6O\/TkQwzAVfTfuz9IP3t+PW3bfDPdf+c1Ivz50K3LaWLsenFnSAESVIbuMXi7T4BG5+iC1bfjQSBCFx6lWVCe0NxyfLFaAHD9tuj00doSmQitNE+gRnvDU4nyVGilPl2ogkMzBZ4GigqxvM+Q\/Fb7ou0bcO2G\/fvPtwoC+znBDdctF7dFP8ux\/nUdsc1PjPlr1afnzN8R2EKP2o\/uJF34+rYSiRyd7VHTEzyPxl2a80Iht1PDhMehiBCxXh6LQuxrnsArv98ThEKg5TGuOUy0ehvC0ihg9bKj0g4QuNGukLStgiDoifEDzqg\/49wKPfniH3iT4SiBxzkXbXhd+O62G3pI8UVNjGUnivhbpfM61o2xdW8gwPAmnOZ5I4a3RBbLE8g5hgLEqEsHzGmfqEt5L6s9gfmNsqWNdCi8a+4f1aNtH5y+VRDYnoD344g6aZrojtAhUCOyG06Mz85F3x1SnW+J1q\/PFbp3J8cTnOx8IU4VuvhzAPs5RDwIzLaP2VByG1WY4wlYtU\/WbbRHeiX9GmX+rmMXL\/TTvQmn5XpE6OZeIwOnDwS+baQNVPnaZ6sgiBPPJxV8UPo4hs+SJk1HZ6lv2PO2CoIgwRZxrDjRFB8aFNf28JG46joBgfXEOA8oqu5U1J8MOEAACAbc0k0mqCYCONQQNLFD0ObyoRsKCPCSjvKFMyywDs1LOvC6JkCQFsqheV0TXtwHCNJAMFQv7uOvmeIVrgAhLggs\/qF7hav6rjV7BA6NeI7Akx2ssEGQBlgfrJOmvrpV6d34PYE6iM9gC8zMzASfwNFGWwAQJOg+QJDAWA1KCggSdBYgSGCsBiUFBAk6CxAkMFaDkgKCBJ21f\/\/+BKmRtCkWAAQJegqeIIGxGpQUECToLECQwFgNSgoIEnQWIEhgrAYlBQQJOgsQJDBWg5ICgpiddenSJQIEMY3VsGSAIEGH7dixg956660EOZC0CRYABAl6ae\/evXT69OkEOZC0CRYABAl66dixY3TkyJEEOZC0CRYABAl66dy5c7R9+3Y6f\/58glxIWncLAIKEPcTfn5+fn0+YC8nrbAFAkKJ39u3bRxwaYRkOCwCCFP3Iv7zavXs3QEhhuzpmAQQpe4VBYI\/AoRHmCCmNWJNsgCBjR\/AcgSfLfNeIb5+GPUfgh21Y6mkBQJBDv\/BdI54j8HMEfqDG2\/x02V75HKfh85wHSz0sAAhK7Af2Euwt2Guw92AvgqV6CwCCivqA5xE8n+B5Bc8vsFRnAUBQne1FzRwa8Z0mgFBdRwCC6mzv1cwgsEfAUo0FAEE1du+rlUMjzBH6zFLKAUBQipkHV8JzBJ4s467RYFvlnQIQ5G3RDOXxXSMOjbCUawFAUK69I2vj26f8HAFLuRYABOXaO7I2fo7AD9SwlGsBQFCuvQfWhnBooIlyTwAIcjdptgLxY\/5s9kuTGxCksVqBeQBBgcYNKRoQhBimqsOAoHzLA4LybR5ZI\/70N9I8hZwEBIWYNX2h8ATpbZc2JyBIa7mC8gGCggwbUSwgiDBOFacAQflWBwTl29yrkZ8J2OuuXbv6jnkZsFGIBQBBIWaNXyj\/loBH\/6CVnx5fvHgxfmFImcoCgCCV2fLLdOrUqUAAGAo8Pc7PzlElAYIo65R07vDhw30gwAuUZHynGkBQnq1Da7pw4QLt3LnTAAFeINRcuZ8ABLmbNF2BJ06c8CCAF0hnw7S5AEFayxWQ78CBAwIEeIECjBtRJCCIME7Zp86cOSN+T4A7QuVavjIIjh49Stu2baPJyUnasmULVtggUAOsD9YJ66WopRII9uzZQ1NTU+LfFc6ePSv+c4f\/dwcrbGBrgPXB\/8LBemHdFLGUDgETzRcE8UPwtuCj9lkvrJsiPELpELBrY7KjLhjnAEiQBlg3rJ+8l9Ih4BgPXgAiDxL5oGOsG9ZP3kvpEPAkeNDF4jwgCdMA6yfvpTYQvGPLO6mKNczYOF5PEAFBAaBA7PUUe1i\/AIKyIViYptHOKE0vNEsoYQIahuOAABC0fj7VKghGRkaoiNWed0SOjvAEtYOudRDEuQtw\/PjxOMlEGoYqEwQCig51OnKdnBcimZ\/s0OjMoi+YgxPU2TRNi\/Ip+OLMqJ9HO74k0k3QxCYuj8OuRZp2tkcnJ5wwTNUzQfPa0\/TYZf1QhnIzTltkWdxGPb\/RZq2OyIGh4nSAIEDu5UHgCnTioJwf6F7CEr0BBZ\/r+ELmcx0Jj4DAEahX5pJbh59e7hvpVVlB57SyFLBGXh9WFwZVVnPmPICgUggsoQhxj8pJ8zxNeBNofXuJDCB4FBXilOKzAFmSEOgjtA6Nvi1Gaz2\/vu3Vo9qn6tX27fQVj\/BxvQ8gqBgCIUIVpmwaNe4ceWJnkW9SoZAcrVUe71OKsU+IbvpgCPrPuZ4kBCjdUwVB0Ve3BXlNoQAEVUIQR1SO+Oed+N8Wsb5vjHh9QuwXuj7669vwBAFiSHmotk+MeRIbZyltTiAg8GNu1yvIEV2MmhwGuZNZP8Z3RldL6EYsbp0bFA6ZZbnAmPMLLcaPA602VzHgrKkX4DbCE0gqfvWrX4mX3D322GM0OjpK\/PnCCy8QH49ast4dcoWvhO6KXhe8e14TohSTfkfGvQskQ4+kEDjlGWU5nkfdgTIBCZgD2FD01Y1wKEo7uZ5jkoNGHfvWZZgneOaZZ2j16tX0wAMP0HPPPUfPPvus+OT9a6+9lvh82JIYgoQjohCouhuTMG+QTXCsH8zWe4JHH32U7r77bvrFL37h6VwPh\/g4n+d0QUuxELjhie4ZIOJ+EWe1SasheOqpp+iee+7p07YOgTrJ6Ti9vRQGgZwvePE5vECgt88KAOdvLQSzs7N0ww030C9\/+Utb1xQEwRtvvEH33nsvPfHEE0b6wiCA6AsTvQ1O6yA4efIkPfnkk7R27Vp67bXXDEGrnSAI+NyPfvQjuu+++8Tc4cUXXyT+z09AkH94You06P3WQbBu3Tpx54cFHLaEQaDS88T5wQcfFHOFxBCcnKPxsS71Ch\/pe9QdG6OxrT1jRF2YHe87VrTIRPn6dfe6NLZ5jhZS2YCva5zmTuYHX+sgYIHnudYeAkswtYAglfiV6AGBGoyNTyY5aDSLe4vUKMzZGeQJ9PRZIRCi5BFbrHKEs0dKHkW9kXOB5jar9GPU7UlxiJF23EnH59jTuGLpbnVGfi\/vEvVBwHWp+r10bh3jm528zrluz93vzrIXc+sen12g3lbVDt2zSQ+kylSeKMgTiGOqDPnptSGoHP3a8\/MGrfMEuoDDtkuDQAjQF5AQlRCNOdqxcFl0DLqfxhG\/yC\/FIAXlQSEhmDspBSxhMSAw8kiBifr1bYZM7iuBSnDcNrnn+redfKJ8vX3yWjm\/KkvzCnxtA8vxrkvCr+UPGgjjHAMEASSUBoHVgbpAWRCuoFlkatRzR0df6K4Axb4uOFGuBpIGm16HgEgXo5dOF7YPgQLRFbcJr3fOuCatDaJ94RAYcBtlcP1aOcZ2PiAAgkohcMXmhSMcQqjwgQXJ2yweT6guBEZ6J48QoC4yGwJnX42yOgRi2yvbEZRXhgaXKMva99K5IlRli1FXgKSHOIM9QV87uM6wcgBBgGKdQ02dE9idrwvUHf26NKeFQuaIaI2CljD70orz4yTmCDpoOgSWJwj0OCxQqy4fAhdSP582gut5uB5Vr74tgOPriigHEAwzBHKUVwJ1BCFCBOvujjim0ghhybBJF5kQkyZAKS4Bme5t9Pwq7hdlWyO\/POeJ26orDAK3vghP4EFnAW1BYJQDCLJDwHdz8l7tu1CRkzFDQFL44k6KEy\/bo6K9L8RshlBeLG6Uq0ZTNZdQIpN5FURcnhCifWcmLQTy7pO4Hg7TeuJOlj9nMecEP+RnFjKt\/+mm8YB1zhvlKFjV4GDZiPN5NrHhlYOB3T+tmhPYYi1q3zZy2n1\/hFUixmdaW0blAwRl\/+9QyGhkdpIcsVXcHCsPADFtGN8egKCWEMTvwLQdj3y+jQEBIBAP4doMxVBD0OaOxbX7I\/0gWwwFBHhJR\/wOHySItp0fmpd04HVNgCAtvEPzuia8uA8QpIFgqF7cx4\/Q8ApXgBAXBBb\/0L3CVT1HZo\/AoRHPEXiygxU2CNIA64N1UsSrW5UWS\/8HOlUxPoMtMDMzE3wCRwuzACAozLTpCgYE6eyWJRcgyGK9AvICggKMOqBIQDDAQGWfBgRlW5wIEJRv88ga9+\/fH3keJ\/O3ACDI36aZSoQnyGS+VJkBQSqzFZcJEBRn27CSAUGYZSo6DgjKNzwgKN\/mkTUCgkjzFHISEBRi1vSFAoL0tkubExCktVwB+d5++23x2qkCikaRERYABBHGKfvUm2++Sd\/5znfKrrb19QGCGkng9ddfp1deeaVGLWpHUwBBjfr5yJEj9JOf\/KRGLWpHUwBBjfqZQ6Ff\/\/rXNWpRO5oCCGrSz\/zmzX379tWkNe1qBiCoSX+\/\/PLLxHMCLOVbABCUb\/O+Gvnng4cOHeo7jgPlWAAQlGPnwFp+85vfiN\/Pshc4d+5cYBocLN4CgKB4Gxs1nD9\/nl599VXi18ryytt8DEt1FgAEJdqeR3se9Tn8YS+ApR4WAAQl9gPH\/QwAlnpZABCU1B9854e9AJb6WQAQlNQn\/AyAnwVgqZ8FAEEJfcJPgfHFuBIMnbIKQJDScEmy8feB+HtBWOppAUBQQr\/wN0PxNLgEQ6esAhCkNFySbBwK8W8FsNTTAoCghH554YUXiH81hqWeFgAEJfTLsWPHSqgFVaS1ACBIa7kE+fDj+QTGqiApICjB6ICgBCNnqAIQZDBe3KyAIK6lqkkHCEqwOyAowcgZqgAEGYwXNysgiGupatIBghLsDghKMHKGKgBBBuPFzQoI4lqqmnSAoAS7A4ISjJyhCkCQwXhxs+LtM3EtVU06QFCC3eEJSjByhioAQQbjxc0KCOJaqpp0gKAEuwOCEoycoQpAkMF4QVn5y3L2umvXrr5jQXlxrBoLAIIC7L57927i0T9o3bFjB128eLGAWlFkWgsAgrSWi8h36tSpQAAYCnytOsJwFZ0CBAUZ\/vDhw30gwAsUZOyMxQKCjAYMy37hwgXauXOnAQK8QJi1qj0OCAq0\/4kTJzwI4AUKNHTGogFBRgMOyn7gwAEBArzAIEtVdx4QFGz7M2fOELxAwUbOWHyuEBw9epS2bdtGk5OTtGXLFqywQaAGWB+sE9ZLHZbcINizZw9NTU2Jf10+e\/YsLS0tYYUNAjXA+uB\/52a9sG6qXnKBgInmC4L4AX6SwY\/1wrqp2iPkAgG7NiY7iQGQFsCwBlg3rJ8ql1wg4BgPXgCiTjOwsW5YP1UuuUDAk+A0BkAegMMaYP1UuRQLwSMraKmKFRPSRg1KgKAISAABIEjgWuAJBgAzP9mhzuR8o0TVtDATnqDmngAQFD9vaRUEIyMjVMTaN+8YMLonGSkBASCIFVkxyYHCskZ5BiDucvz48cik27dvp\/Xr1wuoEkGwME2jnQma4DCn06GJg24nC7E7+3xMD390CPRtvt7FmVHqbJqmxRyhC7TjkJffOk8QqWztZBQEvV6PrrjiCvGkkcFKDkGHRmcWPXBNMS\/S9Cb\/vC58fRsQ5OchAIEmfH0zDII33niDbr75ZnrppZdE8nQQjNL0gupEV\/TKI4iR+OCEN8Lrwte3AYGyX\/ZPQKArX9sOg+BTn\/oUfeMb3\/BSZodgniZUGGR8TtC8E4bowte3AUF28YsBx7ExIPDkbG4EQfDII4\/Qww8\/bCTMDkGAJ9BicF34+jYgAASGEJlkRbXxmePE+Omnn6a77rrLqJd3skPQP8EVYpcTXl34Yu7gTKrZQywtufBgYpwdBniCPlm7B3RPwP\/jc+ONNwa+EDsPCBhcIXYvHFJCN8OhpSU9dHLmFTP+3MGAX\/MkOD4YEkAwAIKf\/vSntGLFCjp06FBgysQQQKDBXrtCuwCCQGkTsSc4d+4cbdiwgZ5\/\/vmQVCnCoQo7G14h2CsAghB5MwT3338\/PfHEEyEp3MPwBMHCahJwgCBE4l\/84hcFBCGnvcOAABB4Yki5Ueq3SFmwcdePf\/zj4qd37BGiVkAACFJq38tWOgRezQM2WPhxlkIh6HVpbPMcLUTOI3rUHRujbq\/5YqwqhEI4FKJ0QNAeqABB2RCcnKPxsXEa3zxGY2Nd6vEoL47xvnaMj3ueYIHmnPT+aM+j\/zjNnWShRnuChdlxWS6XLfN45Uqhc\/2ex3Hrctui1RnU7kgPJctuQBpAUAkEmrgsEfe2OmJVgvTEmhICzq9Ac8Qoyt7ak+AoiJaIQRmfXRD37\/00EkIFjgTVB7E5Ih8UZgGCSiDwBShGe02orleQHiIrBNYoLLyCgMAFwhU0A6baY3sVDT7pCVzvMzwAMCCAoBIIpMhZpGK0VqGQ+rTDFk2MQthxwyE3nwptxKeEQNTL20Yo5EJgpHdCNOElBARauy3ABo22dT4PCOoAgQp\/bGGFeQJjVLZHb3+UFiO\/VrbuCdy5RJfmtFDIPaa8gl+OEDAgCFFK9sPtu0XaJyZTxEKoKjyyIBiTo7ibRonVzK+PuCYEcpRXnsABTsT\/KuaXABpzAtFWOX\/pa7cFiQ1wg\/Zb5wniPixLki7RzyuDxCTF5oYhStwyVFIjuZZmfHau7+6QHcK48b4Uvrrr5EElBWzvC+GaIZSaMBtzlQYJXB8UwrZbBUGfWK3fG+R2viEi4VHfE3lD2hwm5CzHAUERINReUHK0V16m9u0tNvQCBK2EoFhRZRmVq8gLCABB7X7kUjYIww1By9182WJqan1DAQFe0oHwJi2AQ\/OSDryuCRCkhWBoXteEF\/cBgjQQDNWL+\/jBNV7hChDigsDiH7pXuKpvb7BH4NCI5wg82cEKGwRpgPXBOqn61a1Kt7l8d0gVhk9YoIkWAARN7DW0OVcLAIJczYnCmmiB\/weNwQqANb1LswAAAABJRU5ErkJggg==","width":193}
%---
