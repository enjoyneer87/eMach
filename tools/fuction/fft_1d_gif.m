function fft_1d_gif(file_name,data,p)
load(file_name);

for i=1:height(data)
    clf;
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
    bar(fft_Br(1:124));
    xticks(ticks)

% %     formatter
    set(gca,'FontName','Times New Roman','FontSize',12)
    xlabel('Wavenumber','FontName','Times New Roman', 'FontSize',12,'FontWeight','B');
    ylabel('B_{rad}[T]','FontName','Times New Roman', 'FontSize',12,'FontWeight','B');
    box on
    title('Spatial FFT Br')
    text(80,0.5,strcat("Time","[sec]-",num2str(time(i)) ));
    drawnow limitrate
    getframe(gcf); 
end
end
