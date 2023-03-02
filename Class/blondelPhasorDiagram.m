function blondelPhasorDiagram(input_obj) 

% freq (Hz, 1/s)
freq_e=input_obj.ShaftSpeed/60*(input_obj.p/2); 
freq_mech=input_obj.ShaftSpeed/60;
One_mech_Endtime=1/freq_mech;
One_elec_Endtime=1/freq_e;


% omega (rad/s)
omega_mech=freq_mech*2*pi;
omegaE=freq_e*2*pi;


xx=input_obj.RMSPhaseResistiveVoltage_D+input_obj.RMSPhaseReactiveVoltage_D
yy=input_obj.RMSBackEMFPhase+input_obj.RMSPhaseResistiveVoltage_Q+input_obj.RMSPhaseReactiveVoltage_Q;
% beta=[]; % Phase advance \beta I or \phi
beta.theta=rad2deg(pi/2+atan(input_obj.RMSPhaseCurrent_D/input_obj.RMSPhaseCurrent_Q))
beta.spandeg=[0,beta.theta]
% PFangle=[]; % PFangle, \theta V-I or \varphi
theta.theta=rad2deg(atan(input_obj.RMSPhaseCurrent_D/input_obj.RMSPhaseCurrent_Q)-atan(xx/yy));
theta.spandeg=[beta.theta,beta.theta+theta.theta];

% \delta = beta+PFangle 

Angdelta.theta=theta.theta+beta.theta
Angdelta.spandeg=[0,theta.spandeg(2)]


alpha.theta=rad2deg(acot(input_obj.FluxLinkageLoad_D/input_obj.FluxLinkageLoad_Q)) % flux linkage angle
alpha.spandeg=[0-90,alpha.theta-90];

% quiver axis
% !!!!!! important 'off' in quiver is autoscale must be included
quiver(0,0,1000,0,'off','k',LineWidth=1,MaxHeadSize=0.05)
hold on
quiver(0,0,0,1000,'off','k',LineWidth=1,MaxHeadSize=0.05)
hold on
quiver(0,0,-1000,0,'off','k',LineWidth=1,MaxHeadSize=0.05)
data_type=2 % 1 : pk plot 2: rms plot


% current
if data_type==1 %rms motorcad phasor diagram
    %jmagdata type idmean iqmean - peak? - should fft
    dqplane=figure(1)
    quiver(0,0,input_obj.PkPhaseCurrent_D(1),0,'off','y',LineWidth=3)
    text(2/3*(input_obj/PkPhaseCurrent_D(1)),-10,'Id')
    hold on 
    quiver(0,0,0,input_obj.PkPhaseCurrent_Q(1),'off','y',LineWidth=3);
    text(10,2/3*(input_obj.PkPhaseCurrent_Q(1)),'Iq')
    hold on
    quiver(0,0,PkPhaseCurrent_D(1),PkPhaseCurrent_Q(1),'off','y',LineWidth=3);
    text(2/3*(PkPhaseCurrent_D(1)),2/3*(PkPhaseCurrent_Q(1))+10,'I_{fund}')
    hold on
    formatter_sci_phasor_diagram
%     groot_setting


% current 
elseif data_type==2
dqplane=figure(1)
quiver(0,0,input_obj.RMSPhaseCurrent_D,0,'off','b',LineWidth=3);
text(2/3*(input_obj.RMSPhaseCurrent_D),-10,strcat(num2str(input_obj.RMSPhaseCurrent_D),'    ', 'I_d_{rms}[A]'))
hold on 

quiver(input_obj.RMSPhaseCurrent_D,0,0,input_obj.RMSPhaseCurrent_Q,'off','b',LineWidth=3);
text(input_obj.RMSPhaseCurrent_D,2/3*(input_obj.RMSPhaseCurrent_Q),strcat(num2str(input_obj.RMSPhaseCurrent_Q),'    ','I_q_{rms}[A]'))
hold on

quiver(0,0,input_obj.RMSPhaseCurrent_D,input_obj.RMSPhaseCurrent_Q,'off','b',LineWidth=3);
sqrt(input_obj.RMSPhaseCurrent_D.^2+input_obj.RMSPhaseCurrent_Q.^2)==input_obj.RMSPhaseCurrent
text(2/3*(input_obj.RMSPhaseCurrent_D),2/3*(input_obj.RMSPhaseCurrent_Q)-10,strcat(num2str(input_obj.RMSPhaseCurrent),'    ','I_{rms}[A]'))

% beta plot
% [betaplot,beta.x,beta.y]=ang([0,0],yy*10,deg2rad(beta.spandeg),'r')
% text(beta.x(50),beta.y(50),'\beta','FontSize',20)
formatter_sci_phasor_diagram

% voltage
absReativeVoltage=sqrt(input_obj.RMSPhaseReactiveVoltage_D.^2+input_obj.RMSPhaseReactiveVoltage_Q.^2);

% Voltage plot
%Plot BEMF
quiver(0,0,0,input_obj.RMSBackEMFPhase,'off','r',LineStyle='--');
text(0,input_obj.RMSBackEMFPhase*2/3,strcat(num2str(input_obj.RMSBackEMFPhase),'    ', 'E BEMF phase_{rms}[V]'))
hold on

%Express Resitive RMSPhaseResistiveVoltage with  - need RMSBackEMFPhase RMSPhaseResistiveVoltage_D RMSPhaseResistiveVoltage_Q
quiver(0,input_obj.RMSBackEMFPhase,input_obj.RMSPhaseResistiveVoltage_D,input_obj.RMSPhaseResistiveVoltage_Q,'off','r');
text(input_obj.RMSPhaseResistiveVoltage_D,input_obj.RMSPhaseResistiveVoltage_Q+input_obj.RMSBackEMFPhase,strcat(num2str(input_obj.RMSPhaseResistiveVoltage),'    ', 'Phase D Voltage_R'))
hold on

%Plot Q drop
quiver(input_obj.RMSPhaseResistiveVoltage_D,input_obj.RMSBackEMFPhase+input_obj.RMSPhaseResistiveVoltage_Q,0,input_obj.RMSPhaseReactiveVoltage_Q,'off','r');
text((input_obj.RMSPhaseResistiveVoltage_D+0)/2,(input_obj.RMSBackEMFPhase+input_obj.RMSPhaseReactiveVoltage_Q/3*2),strcat(num2str(input_obj.RMSPhaseReactiveVoltage_Q),'    ', 'Phase VoltageQ_{Reactive}'))
hold on

%Plot D drop
quiver(input_obj.RMSPhaseResistiveVoltage_D,input_obj.RMSBackEMFPhase+input_obj.RMSPhaseResistiveVoltage_Q+input_obj.RMSPhaseReactiveVoltage_Q,input_obj.RMSPhaseReactiveVoltage_D,0,'off','r');
text((input_obj.RMSPhaseResistiveVoltage_D+input_obj.RMSPhaseReactiveVoltage_D)/3*2,(input_obj.RMSBackEMFPhase+input_obj.RMSPhaseReactiveVoltage_Q+10),strcat(num2str(input_obj.RMSPhaseReactiveVoltage_D),'    ', 'Phase VoltageD_{Reactive}'))
hold on

%%Plot Voltage_s
quiver(0,0,xx,yy,'off','r');
%theta plot
% [thetaplot,theta.x,theta.y]=ang([0,0],yy*10,deg2rad(theta.spandeg),'b')
% text(theta.x(50),theta.y(50),'\theta','FontSize',20)

%delta plot
% [deltaplot,Angdelta.x,Angdelta.y]=ang([0,0],sqrt(xx.^2+yy.^2),deg2rad(Angdelta.spandeg),'b')
% text(Angdelta.x(50),Angdelta.y(50),'\delta','FontSize',20)


text(2/3*xx,2/3*yy,strcat(num2str(input_obj.PhasorRMSPhaseVoltage),'Phase Terminal Voltage_{rms}[V]'))
input_obj.PhasorRMSPhaseVoltage == sqrt(xx.^2+yy.^2)

% flux linkage
quiver(0,0,1000*input_obj.FluxLinkageLoad_D,0,'off','g',LineWidth=2);
hold on
[alphaplot,alpha.x,alpha.y]=ang([0,0],input_obj.FluxLinkageLoad*30,deg2rad(alpha.spandeg),'b')
% text(alpha.x(50),alpha.y(50),'\alpha','FontSize',20)

hold on
quiver(1000*input_obj.FluxLinkageLoad_D,0,0,1000*input_obj.FluxLinkageLoad_Q,'off','g',LineWidth=2);
hold on
quiver(0,0,1000*input_obj.FluxLinkageLoad_D,1000*input_obj.FluxLinkageLoad_Q,'off','g',LineWidth=2);
hold on

Venom=[114,140,0]./255;
quiver(0,0,1000*input_obj.FluxLinkageQAxisCurrent_D,0,'off','Color',Venom);
hold on
quiver(1000*input_obj.FluxLinkageQAxisCurrent_D,0,0,1000*input_obj.InductanceXCurrent_Q,'off','Color',Venom);
hold on
quiver(1000*input_obj.FluxLinkageQAxisCurrent_D,1000*input_obj.InductanceXCurrent_Q,1000*input_obj.InductanceXCurrent_D,0,'off','Color',Venom);

% Inductacne voltage drop
VinductanceDropDaxis=-omegaE*input_obj.InductanceXCurrent_Q/sqrt(2);

VinductanceDropQaxis=omegaE*input_obj.InductanceXCurrent_D/sqrt(2);

Vy=input_obj.RMSBackEMFPhase+input_obj.RMSPhaseResistiveVoltage_Q
Vx=input_obj.RMSPhaseResistiveVoltage_D;
quiver(Vx,Vy,VinductanceDropDaxis,0,'off','Color', [.5 0 .5]);
hold on


quiver(Vx+VinductanceDropDaxis,Vy,0,VinductanceDropQaxis,'off','Color', [.5 0 .5]);
hold on
quiver(Vx,Vy,VinductanceDropDaxis,VinductanceDropQaxis,'off','Color', [.5 0 .5])
% hold on
% input_obj.RMSPhaseResistiveVoltage_D
% input_obj.RMSPhaseReactiveVoltage_D
% VinductanceDropDaxis

%% Power 
% qinfund=sqrt(2).^2*(3/2)*(yy*input_obj.RMSPhaseCurrent_D-xx*input_obj.RMSPhaseCurrent_Q)/1000; %KVAR
% pinfund=sqrt(2).^2*(3/2)*(yy*input_obj.RMSPhaseCurrent_Q+xx*input_obj.RMSPhaseCurrent_D)/1000; %KW
% PFangle.theta=rad2deg(atan(qinfund/pinfund));
% PF=cos(deg2rad(PFangle.theta));
% Sinfund=sqrt(qinfund.^2+pinfund.^2);         %KVA
% % synch
% % quiver(0,0,-pinfund,qinfund+yy,'off','y',LineWidth=3);
% % hold on
% % quiver(0,0,-pinfund,yy,'off','y',LineWidth=3);
% % hold on
% % quiver(-pinfund,yy,0,qinfund+yy,'off','y',LineWidth=3);

% % % on d axis
% quiver(0,0,pinfund,qinfund,'off','y',LineWidth=3);
% hold on
% quiver(0,0,pinfund,0,'off','y',LineWidth=3);
% hold on
% quiver(pinfund,0,0,qinfund,'off','y',LineWidth=3);
fontsize(gcf,scale=1.5)
fontname(gcf,"Times New Roman")

end

end