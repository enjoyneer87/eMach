function dq_phasor_diagram(input_obj) 
% quiver axis
quiver(0,0,1000,0,'off','k',LineWidth=1,MaxHeadSize=0.05)
hold on
quiver(0,0,0,1000,'off','k',LineWidth=1,MaxHeadSize=0.05)
hold on
quiver(0,0,-1000,0,'off','k',LineWidth=1,MaxHeadSize=0.05)
plot_type=1


Nd=length(input_obj.Id);
Nq=length(input_obj.Iq);
fftd=input_obj.FFT_Idq.Id;
fftq=input_obj.FFT_Idq.Iq;
PkPhaseCurrent_D=real(fftd)/Nd;
PkPhaseCurrent_Q=real(fftq)/Nq;
% current
if plot_type==1 %peak  %jmagdata type idmean iqmean - peak? - should fft
    dqplane=figure(1)

    quiver(0,0,PkPhaseCurrent_D(1),0,'off','y',LineWidth=3)
    text(2/3*(PkPhaseCurrent_D(1)),-10,'Id')
    hold on 
    quiver(0,0,0,PkPhaseCurrent_Q(1),'off','y',LineWidth=3);
    text(10,2/3*(PkPhaseCurrent_Q(1)),'Iq')
    hold on
    quiver(0,0,PkPhaseCurrent_D(1),PkPhaseCurrent_Q(1),'off','y',LineWidth=3);
    text(2/3*(PkPhaseCurrent_D(1)),2/3*(PkPhaseCurrent_Q(1))+10,'I_{fund}')
    hold on
    formatter_sci_phasor_diagram
%     groot_setting
% voltage

% flux linkage


else     
    quiver(0,0,PkPhaseCurrent_D,0,'off','b');
%     quiver(0,0,)
    hold on 
    quiver(PkPhaseCurrent_D,0,0,PkPhaseCurrent_Q,'off','b');
    hold on
    quiver(0,0,PkPhaseCurrent_D,PkPhaseCurrent_Q,'off','b')
end