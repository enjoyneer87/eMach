function [mag_fft_V_c]=plot_2d_fft_positive(data_2d,p,unit)

%% with frequency space grid
fft_Br = fft2(data_2d);   %% Matlab 내장 함수 - 2d FFT
n_time=size(data_2d,1);
n_angle=size(data_2d,2);

mag_fft_V_c=2*abs(fft_Br)/(n_time*n_angle); % Normalize
% sf_fft_Br = 2*abs(fftshift(fft_Br))/(n_time*n_angle); % Shift and Normalize

h_magBr=size(mag_fft_V_c,1); 
l_magBr=size(mag_fft_V_c,2); 

x_seq=[1:1:h_magBr/(p*2)];
y_seq=[1:1:l_magBr/(p*2)];

x_flip=1;
    if x_flip==1
        x_seq=flip(x_seq);
        order_fft_Br=mag_fft_V_c(x_seq,y_seq);
    else
        order_fft_Br=mag_fft_V_c(x_seq,y_seq);
    

    end    
%%plot 
figure(1)
axis equal

imagesc(order_fft_Br)
YTicklabel_normal=[0:p:h_magBr/(p*2)];
YTicklabel_flip=flip(YTicklabel_normal);
set(gca,'xgrid', 'on', 'ygrid', 'on', 'gridlinestyle', '-');
ax=gca;
ax.GridColor=[1, 1, 0.1];
% if varargin=='Unit'
    c=colorbar;
    c.Label.String = unit; 
% else 
%     colorbar
% end
 set(gca,'fontweight','bold','YTick',[0:p:h_magBr/(p*2)],'YTickLabel',YTicklabel_flip, ...
'XTick',[1:p:l_magBr/(p*2)],'XTickLabel',[0:p:l_magBr/(p*2)]);

xlabel('Mech Order')
ylabel('Wavenumber')
end