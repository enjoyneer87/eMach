function fft_1d_gif(file_name,data,p,orderEnd)
load(file_name);

% for i=1:height(data)
%     clf;
i=1
    B_rad_X = fft(data(i,:)); 
    N=length(data);
    Side = B_rad_X(1:N/2);
    fft_Br = abs(Side)/(N/2);
    
    if p == 6
    ticks=[0 : 6 : 124];
    else
    ticks=[0 : 4 : 124];
    end
    
%     figure 
    bar(fft_Br(1:orderEnd));
%     xticks(ticks)

% %     formatter
    set(gca,'FontName','Times New Roman','FontSize',12)
    xlabel('Order','FontName','Times New Roman', 'FontSize',12,'FontWeight','B');
    ylabel('Voltage[V]','FontName','Times New Roman', 'FontSize',12,'FontWeight','B');
    box on
%     title('Spatial FFT Br')
%     text(80,0.5,strcat("Time","[sec]-",num2str(time(i)) ));
%     drawnow limitrate
%     getframe(gcf); 
% end
hold on
end
