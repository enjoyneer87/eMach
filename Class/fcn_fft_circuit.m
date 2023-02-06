function X=fcn_fft_circuit(data,waveform,PN)
    X=fft(waveform);
    N=length(waveform);
    if PN==1 %Positive=1 all=0
    %Positive Side
    Side = X(1:N/2);
    amp_X = abs(Side)/(N/2);
    else 
    amp_X = real(X)/N;
    end
    
    if data.p == 12
    ticks=[1 : 1 : 180];
    xlabels=[0:1:180];
    else
    ticks=[0 : 4 : 124];
    end
   
    bar(amp_X(1:181));
    xticks(ticks)
    xticklabels(xlabels)
    
    xlabel('Order','FontName','Times New Roman', 'FontSize',12,'FontWeight','B');

end