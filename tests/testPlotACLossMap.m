%% 여기에는 포함안되어있음
SatuMapFilePath='Z:\Simulation\ACCESS2023\HDEV_Model2Temp115v2.mat'
load(SatuMapFilePath)

%% 
% ':' 기준으로 문자열 분리

% 결과 출력
% disp(num_arr);


ACConductorLossProportion_Lab='0.00449155370201 : 0.00911130913316 : 0.0153789752007 : 0.0245892589602 : 0.0432640773071 : 0.0660962367977 : 0.1014559291 : 0.148112265486 : 0.209136274834 : 0.378364119479 : 0'
input_str=ACConductorLossProportion_Lab
str_arr = strsplit(input_str, ':');

% 문자열 배열을 숫자 배열로 변환
ACConductorLossProportion_Lab = str2double(str_arr);
length(ACConductorLossProportion_Lab)
% MagLossArray_MotorLAB=


LossModel_AC_Lab='6.23629867623E-5 : 9.28873584191E-5 : 9.6038999614E-5 : 9.97807788197E-5 : 0.000119918852616 : 0.000124725973525 : 0.000128949071539 : 0.000405705451353 : 0.00236121231102 : 0.139086248854 : 3.76422799671 ; 6.23629867623E-5 : 9.28873584191E-5 : 9.6038999614E-5 : 9.97807788197E-5 : 0.000119918852616 : 0.000124725973525 : 0.000128949071539 : 0.000405705451353 : 0.00236121231102 : 0.139086248854 : 3.76422799671 ; 6.23629867623E-5 : 9.28873584191E-5 : 9.6038999614E-5 : 9.97807788197E-5 : 0.000119918852616 : 0.000124725973525 : 0.000128949071539 : 0.000405705451353 : 0.00236121231102 : 0.139086248854 : 3.76422799671 ; 6.23629867623E-5 : 9.28873584191E-5 : 9.6038999614E-5 : 9.97807788197E-5 : 0.000119918852616 : 0.000124725973525 : 0.000128949071539 : 0.000405705451353 : 0.00236121231102 : 0.139086248854 : 3.76422799671 ; 6.23629867623E-5 : 9.28873584191E-5 : 9.6038999614E-5 : 9.97807788197E-5 : 0.000119918852616 : 0.000124725973525 : 0.000128949071539 : 0.000405705451353 : 0.00236121231102 : 0.139086248854 : 3.76422799671 ; 0.01948801761 : 0.0609950529198 : 0.0950910822152 : 0.194426589309 : 0.299965518162 : 0.470767523014 : 0.664998247645 : 1.02374252212 : 1.32572277978 : 2.0309020498 : 9.16446211988 ; 0.0115379840575 : 0.0631239368278 : 0.106645072773 : 0.226562236388 : 0.354670782638 : 0.561595558149 : 0.795640319329 : 1.22517789296 : 1.58473092848 : 2.33024456653 : 8.78774754084 ; 0.00689402030995 : 0.0674605129751 : 0.118523974491 : 0.257184957408 : 0.40459159197 : 0.641511156239 : 0.90637013476 : 1.39270525054 : 1.79747346981 : 2.54343222418 : 7.98844859381 ; 0.00595358646958 : 0.0694139114616 : 0.124154728566 : 0.269096911509 : 0.423767042407 : 0.674080777904 : 0.951008423207 : 1.45370386766 : 1.87770421337 : 2.58310471874 : 6.69095319201 ; 0.00596605906693 : 0.0692659560606 : 0.123798012282 : 0.268209486208 : 0.420793469342 : 0.666867699547 : 0.944353723692 : 1.43754135035 : 1.86901434887 : 2.55001490316 : 6.00337074527 ; 0.172936719824 : 0.259570170374 : 0.330025549576 : 0.609344378246 : 0.912036954657 : 1.41663928945 : 1.9902888307 : 3.06103806273 : 3.99676874719 : 5.85448373995 : 18.1925302264 ; 0.0780052868553 : 0.238426850451 : 0.370088779532 : 0.756163063461 : 1.17959077317 : 1.86706413958 : 2.65130397749 : 4.1008136887 : 5.35927023993 : 7.59370365031 : 19.7094485884 ; 0.0327937844656 : 0.248701710677 : 0.434549657169 : 0.937441664271 : 1.48470970178 : 2.36263184557 : 3.35609425224 : 5.1756420094 : 6.70619580145 : 9.19931442634 : 20.1070299447 ; 0.0227558381163 : 0.272858754762 : 0.488611506763 : 1.06323841028 : 1.67619881933 : 2.66380062382 : 3.77296514117 : 5.76634601915 : 7.45454255606 : 9.96205812196 : 17.9877653659 ; 0.0223891437542 : 0.271386214073 : 0.485772743606 : 1.05597000417 : 1.66240991207 : 2.64411646469 : 3.74069169358 : 5.70270997353 : 7.40136813373 : 9.80969509842 : 15.8548122996 ; 0.637602502684 : 0.696929645089 : 0.705095884491 : 1.09006073088 : 1.53638059178 : 2.30016537767 : 3.20128687411 : 4.93659604418 : 6.53618472299 : 9.59808501537 : 26.0264934596 ; 0.303789233169 : 0.52519987409 : 0.711644621731 : 1.3638286301 : 2.09137211324 : 3.29668730763 : 4.68955403235 : 7.28893062522 : 9.58776181552 : 13.568206254 : 30.8898868599 ; 0.103423608753 : 0.48699172115 : 0.815840700013 : 1.73583195333 : 2.73334703916 : 4.36357479136 : 6.22252489191 : 9.64847474057 : 12.6298283553 : 17.3388861595 : 34.1327431037 ; 0.0505397959787 : 0.561920181947 : 1.00453550721 : 2.18413451997 : 3.46334875664 : 5.52816518057 : 7.85869722074 : 12.0957556484 : 15.7035938867 : 20.9758363663 : 35.0134560466 ; 0.0492709170747 : 0.606069676178 : 1.0890086673 : 2.36581848019 : 3.73215240695 : 5.92797678926 : 8.38698928997 : 12.806911884 : 16.6090961681 : 21.9099579714 : 32.956158072 ; 1.52909303954 : 1.47783181128 : 1.30679892597 : 1.73578518109 : 2.26717674305 : 3.19468243588 : 4.32117490949 : 6.55573311637 : 8.70328647418 : 12.8334075101 : 32.5680739763 ; 0.843300578221 : 1.07712420625 : 1.22009067643 : 2.06286969221 : 3.02609313141 : 4.64860834574 : 6.56045047554 : 10.2491215362 : 13.6135538388 : 19.3509822673 : 41.0099574974 ; 0.330345055945 : 0.857799859173 : 1.29642609038 : 2.62445275341 : 4.10865255114 : 6.56373341815 : 9.39645084655 : 14.6796873178 : 19.2773184478 : 26.4526821178 : 48.6429222209 ; 0.106195019885 : 0.877231506173 : 1.55011934416 : 3.36944972409 : 5.34318682941 : 8.57099198493 : 12.249790408 : 19.0001559067 : 24.8257133967 : 33.2948211925 : 53.8064481024 ; 0.0862363696014 : 1.02882242418 : 1.84459674402 : 4.03187560578 : 6.38209695619 : 10.1842919921 : 14.4647162577 : 22.1665223215 : 28.7978516383 : 38.0240309722 : 56.0434653895 ; 2.9202308373 : 2.62506147012 : 2.14257520196 : 2.56159896994 : 3.14021176656 : 4.18489279281 : 5.487751663 : 8.11126210704 : 10.6986530736 : 15.7576260792 : 38.4077078035 ; 1.74431768494 : 1.91475932609 : 1.92196239451 : 2.92020485272 : 4.09012421225 : 6.07564944454 : 8.41527583284 : 12.955302826 : 17.2339672425 : 24.6360543322 : 50.1909407241 ; 0.818202386322 : 1.47558049662 : 1.96647834172 : 3.68472330915 : 5.58856620137 : 8.75869019141 : 12.4556513856 : 19.4842816132 : 25.7555835857 : 35.5879249861 : 62.9639711793 ; 0.237738515122 : 1.27265825147 : 2.17958888186 : 4.67063099221 : 7.41754451576 : 11.9203598642 : 17.0892253905 : 26.645579484 : 34.980434803 : 47.0897700171 : 74.0565303811 ; 0.15546593696 : 1.48181015988 : 2.64657914112 : 5.7746541722 : 9.17032515872 : 14.6964004331 : 20.9741682754 : 32.3780935981 : 42.271791842 : 56.0493598472 : 82.0050225475'
input_str=LossModel_AC_Lab
str_arr = strsplit(input_str, ';');

strSt=struct()
% 문자열 배열을 숫자 배열로 변환
for i=1:length(str_arr)
    strSt(i).ACLoss=strsplit(str_arr{i},':');
    strSt(i).ACLoss =str2double(strSt(i).ACLoss)
end
for i=1:length(str_arr)
    for CuboidIndex=1:length(strSt(i).ACLoss)
        AClossMap(CuboidIndex).ACloss(i)=strSt(i).ACLoss(CuboidIndex)
    end
end


%% 오 
%%currentVec
NcurrentVec=5
currentMax=1000;
currentVec=[0:currentMax/(NcurrentVec):currentMax]'
phaseMax=90;
NphaseVec=5
phaseVec=[0:phaseMax/(NphaseVec-1):phaseMax];
old_x=currentVec';
old_x=repmat(old_x,5,1)
     % old_y=AClossMap(CuboidIndex).PhaseAdvance(1,:);
old_y=phaseVec';
old_y=repmat(old_y,1,6)
%% 
for CuboidIndex=length(strSt(1).ACLoss):-1:1
    % Create a matrix with the same size as AClossMap(CuboidIndex).ACloss
    colorData = CuboidIndex*ones(size(AClossMap(CuboidIndex).ACloss)); % 모든 점에 동일한 값 (1) 적용
    
    % Plot surf with fixed color    
     AClossMap(CuboidIndex).ACloss=reshape(AClossMap(CuboidIndex).ACloss,5,6)
     % subplot(length(strSt(1).ACLoss),1,CuboidIndex)
     % old_x=AClossMap(CuboidIndex).Current(:,1);
     Z=AClossMap(CuboidIndex).ACloss;
    surf(old_y,flip(old_x,2), flip(Z,2), colorData, 'DisplayName', [num2str(12-CuboidIndex) 'Cuboid @Temp=65\circ C'])
    % view(90,0)
     % surf(old_x,old_y,AClossMap(CuboidIndex).ACloss,'DisplayName',[num2str(CuboidIndex) 'Cuboid @Temp=65\circ C'])
     % surf(old_x,old_y,AClossMap(CuboidIndex).ACloss)
     hold on
    % surf(old_x,old_y,AClossMap(1).ACloss)

     % intercp_data = interp2(old_x, old_y, (AClossMap(CuboidIndex).ACloss)', new_x, new_y);
     % surf(new_x,new_y,interp_data,'DisplayName','Temp=115\circ C')
     % hold on
     % scatter3(reshape(new_x,[],1),reshape(new_y,[],1),reshape(TempScaledData,[],1),'DisplayName','Temp=65\circ C')
     % ax=gca;
     % ax.ZLabel.String='AC Loss Stator 11th Cuboid [W]';
     legend
     formatterSCI_IpkBeta;
     zlim([0 ,100]);

     % zlim([0 ,max(max(AClossMap(11).ACloss))]);
end

% view(90, 270); % x-축이 왼쪽에 위치하도록 시점 설정 (90도, 270도)
ax = gca; % 현재 그래프의 축 가져오기
% ax.XAxisLocation = 'origin'; % x-축을 원점(0)에 위치
% ax.YAxisLocation = 'origin'; % y-축을 원점(0)에 위치
ax.ZLabel.String='AC Loss of Cuboid [W]';

for i=1:height(AClossMap)
    ACLossMap(i).data=reshape(Map(i,:),6,5)
end


%% AC Loss Temperature and speed Dependencies
speedForCalc=SimulationParameter_MotorLab.SpeedDemand_MotorLAB;
speedForCalc=refSpeed;
refSpeed=ModelParameters_MotorLAB.FEALossMap_RefSpeed_Lab;
% coeffSpeedACLoss=LossParameters_MotorLAB_struct.AcLossFreq_MotorLAB
coeffSpeedACLoss=1.7
coeffTempAcLoss=Losses_At_RPM_Ref.StatorCopperFreqCompTempExponent;
WindingAlpha=ModelParameters_MotorLAB.WindingAlpha_MotorLAB;
WindingTemp=ModelParameters_MotorLAB.TwindingCalc_MotorLAB;
refWindingTemp=ThermalParameters_MotorLAB.WindingTemp_ACLoss_Ref_Lab;

TempScaledData=interp_data;

%% TempScale Map
TempScaledData=TempScaledData.*((speedForCalc/refSpeed)^coeffSpeedACLoss)...
    /((1+WindingAlpha*(WindingTemp-20))/(1+WindingAlpha*(refWindingTemp-20)))^coeffTempAcLoss

%% TempScale Point
SpeedVec=[500:500:5000]
TempVec=[60:20:130]
for TempIndex=1:length(TempVec)
    WindingTemp=TempVec(TempIndex)
    for speedIndex=1:length(SpeedVec)
    speedForCalc=SpeedVec(speedIndex);
    a=TempScaledData(31,19)*((speedForCalc/refSpeed)^coeffSpeedACLoss)...
        /((1+WindingAlpha*(WindingTemp-20))/(1+WindingAlpha*(refWindingTemp-20)))^coeffTempAcLoss
    ACLossVec(speedIndex)=a

    end

    plot(SpeedVec,ACLossVec,'-x','displayname',strcat('Temp=',num2str(TempVec(TempIndex)),'\circ C'))
    
    hold on
end
legend
formatter_sci
ax=gca
ax.XLabel.String='Speed[RPM]'
ax.YLabel.String='AC Loss Stator 1st Cuboid [W]';



% AcLossFreq_MotorLAB
% RacRdc_MotorLAB
% 
% PsiQ_coeff_MotorLAB
% PsiD coeff MotorLAB