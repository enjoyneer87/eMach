%%

HDEV_motorcad=MotorcadData(12);
HDEVdata=DataPkBetaMap(HDEV_motorcad.p);

PmsmFem.NumPolePairs = HDEVdata.p/2;

% object make
HDEV_motorcad.motorcadMotPath='Z:\Thesis\Optislang_Motorcad\Validation'
HDEV_motorcad.motocadLabPath=strcat('Z:\01_Codes_Projects\git_Motor_System_Model\Mathworks_ref\HDEV_fluxmodel\HDEV_Model2','\Lab\');
HDEV_motorcad.proj_path=HDEV_motorcad.motorcadMotPath;
HDEV_motorcad.file_path=HDEV_motorcad.proj_path;

HDEV_motorcad.matfileFindList=what(HDEV_motorcad.motocadLabPath);
HDEV_motorcad.file_name='HDEV_Model2Temp115';
inputobj=HDEV_motorcad;
%% should do manually
inputobj=inputobj.rawPsiDataPost() 
%%currentVec
NcurrentVec=5
currentMax=1000;
currentVec=[0:currentMax/(NcurrentVec-1):currentMax]
phaseMax=90;
NphaseVec=6
phaseVec=[0:phaseMax/(NphaseVec-1):phaseMax];

HDEVdata.phaseVec=phaseVec;
HDEVdata.currentVec=currentVec;
HDEV_motorcad=inputobj;


%% Compare rawModel and Curve 
surf(phaseVec,currentVec,HDEV_motorcad.ModelParameters_MotorLAB.PsiQModel_Lab)
hold on

surf(inputobj.ModelParameters_MotorLAB.PsiDModel_Lab)

%%

%% Raw PsiDModel_Lab import
HDEV_motorcad.rawPsiDataPost()
HDEV_motorcad.ModelParameters_MotorLAB

%% LabModel Import
HDEV_motorcad.proj_path=HDEV_motorcad.motorcadMotPath;
HDEV_motorcad.file_path=HDEV_motorcad.proj_path;

% HDEV_motorcad=motorcadResultExport(HDEV_motorcad)



%  init
ImportPmsmFemParmasVisual




%3d style
%% to check

HDEVdata.plot_xdyq('flux')

td=HDEVdata
%% plot
% kd=find(idVec>-250*sqrt(2) & idVec<-230*sqrt(2))
% kq=find(iqVec>80*sqrt(2) & iqVec<91*sqrt(2))
% for kq=5:55
% fluxDOneElecCheck=squeeze(fluxD(kd,kq,:));
% fluxQOneElecCheck=squeeze(fluxQ(kd,kq,:));
% plot(angleVec,fluxDOneElecCheck*1000);
% hold on
% plot(angleVec,fluxQOneElecCheck*1000);
% % end
% end
% 
% figure;
% mesh(id,iq,lambda_d);
% xlabel('I_d [A]')
% ylabel('I_q [A]')
% title('\lambda_d'); grid on;
% 
% hold on
% figure
% mesh(id,iq,lambda_q);
% xlabel('I_d [A]')
% ylabel('I_q [A]')
% title('\lambda_q'); grid on;
% 
% figure(1)
% mesh(id,iq,FEAdata.torque);
% xlabel('I_d [A]')
% ylabel('I_q [A]')
% title('Torque'); grid on;
% hold on
% figure(2)
% mesh(FEAdata.torque);



figure(3)
sizeFluxMap=size(td.flux_linkage_map.in_d)
for j=1:sizeFluxMap(3)

% j=3
d=td.flux_linkage_map.in_d(:,:,j);
q=td.flux_linkage_map.in_q(:,:,j); 
size(torque)
surf(td.current_dq_map.id,td.current_dq_map.iq,1000*d','FaceAlpha',0.5*abs(31-j)/30)
hold on
title('\lambda_dq'); 
grid on;
ylabel('Iq_{pk}[A]');
xlabel('Id_{pk}[A]');
zlabel('\Psi_{d} [mVs]')
set(gca,'FontName','Times New Roman','FontSize',14)


surf(td.current_dq_map.id,td.current_dq_map.iq,1000*q','FaceAlpha',0.5*abs(31-j)/30)
hold on
grid on;

% hold on


% surf(td.current_dq_map.id,td.current_dq_map.iq,torque,'FaceAlpha',)
% hold on   
ylabel('iq');
xlabel('id');
% dd=td.flux_linkage_map.in_d(:,:,j);
% qd=td.flux_linkage_map.in_q(:,:,j);  
% plot(iqVec,dd*1000)
% hold on
% plot(iqVec,qd*1000)
end
figure
for j=1:sizeFluxMap(3)
    torque=td.torque_map(:,:,j);

    surf(td.current_dq_map.id',td.current_dq_map.iq',torque','FaceAlpha',abs(0.1*9.9*(j-31)/30))
    hold on
    ylabel('iq');
    xlabel('id');
end

