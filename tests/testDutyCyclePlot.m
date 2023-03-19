%% File List Check
clear

close all
DutydatTablepath='Z:\Thesis\Optislang_Motorcad\DutyCycleData'
pathInfo=dir(DutydatTablepath)
% 폴더가 아닌 파일만 추출
isFile = ~[pathInfo.isdir];  % 폴더인지 확인
fileList = pathInfo(isFile);  % 폴더가 아닌 파일 추출


%% Import File
for i=1:4
temptable = readtable(fullfile(DutydatTablepath, fileList(i).name), 'NumHeaderLines', 10);
varName = matlab.lang.makeValidName(fileList(i).name(1:end-4)); % .dat 확장자 제거 후 변수명 생성
dataTable.(varName) = temptable;
end

fieldName = fieldnames(dataTable);

%% Plot DutyCycle

for i=1:4

DutyCycle= dataTable.(fieldName{i});

figure(i);
subplot(2,2,1);
M1Torque=plot(DutyCycle.ElapsedTime,DutyCycle.Torque_Start_,'LineWidth',1);
M1Torque.Parent.YLabel.String='Torque[Nm]';
M1Torque.Parent.XLabel.String='Time[Sec]';
M1Torque.DisplayName='Torque';
formatter_sci;

subplot(2,2,3)
M1RPM=plot(DutyCycle.ElapsedTime,DutyCycle.Speed_Start_,'LineWidth',1);
M1RPM.Parent.YLabel.String='Speed[RPM]';
M1RPM.Parent.XLabel.String='Time[Sec]';
M1RPM.DisplayName='Speed';
formatter_sci;;

subplot(2,2,[2 4])
M1RPM=scatter(DutyCycle.Speed_Start_,DutyCycle.Torque_Start_,'LineWidth',1);
M1RPM.Parent.XLabel.String='Speed[RPM]';
M1RPM.Parent.YLabel.String='Torque[Nm]';
M1RPM.DisplayName='Speed';
title(removeUnderscore(fieldName{i}));


formatter_sci;
end

for i=1:4
figure(i);
subplot(2,2,[2 4]);
hold on
testPlotMaxTorque;
end