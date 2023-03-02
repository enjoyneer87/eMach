function phasor_diagram(input_obj) 
% quiver axis
quiver(0,0,1000,0,'off','k',LineWidth=1,MaxHeadSize=0.05)
hold on
quiver(0,0,0,1000,'off','k',LineWidth=1,MaxHeadSize=0.05)
hold on
quiver(0,0,-1000,0,'off','k',LineWidth=1,MaxHeadSize=0.05)

% current
if plot_type==1 %peak  %jmagdata type idmean iqmean - peak? - should fft
    dqplane=figure(1)
    quiver(0,0,input_obj.FFT_Idq.Id,0,'off','y',LineWidth=3)
    text(2/3*(input_obj.FFT_Idq.Id),-10,'Id')
    hold on 
    quiver(0,0,0,input_obj.FFT_Idq.Iq,'off','y',LineWidth=3);
    text(10,2/3*(input_obj.FFT_Idq.Iq),'Iq')
    hold on
    quiver(0,0,input_obj.FFT_Idq.Id,input_obj.FFT_Idq.Iq,'off','y',LineWidth=3);
    text(2/3*(input_obj.FFT_Idq.Id),2/3*(input_obj.FFT_Idq.Iq)+10,'I_{fund}')
    hold on

    formatter_sci_phasor_diagram
%     groot_setting
% voltage

% flux linkage


else     
    quiver(0,0,RMSPhaseCurrent_D,0,'off','b');
%     quiver(0,0,)
    hold on 
    quiver(RMSPhaseCurrent_D,0,0,RMSPhaseCurrent_Q,'off','b');
    hold on
    quiver(0,0,RMSPhaseCurrent_D,RMSPhaseCurrent_Q,'off','b')
end