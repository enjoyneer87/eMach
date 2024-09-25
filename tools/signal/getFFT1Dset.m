function [P1,P2,bx]=getFFT1Dset(sigData,BoolPlot)
    % Fs = 1000;            % Sampling frequency                    
    % T = 1/Fs;             % Sampling period       
    L = height(sigData);             % Length of signal
    % t = (0:L-1)*T;        % Time vector
    Y = fft(sigData); 
    %
    P2 = abs(Y./L);
    % Postive
    P1 = P2(1:L/2+1,:);
    P1(2:end-1,:) = 2*P1(2:end-1,:);
    % 
    % n = 2^nextpow2(L);
    % Y = fft(sigData,n);
    %%
    %%
    if nargin<2
    % f = Fs/L*(0:(L/2));
    boxvalue=P1(1:30,:);
    bx=boxchart(boxvalue','BoxFaceColor','w','BoxEdgeColor','k','Notch','on','BoxMedianLineColor','r');
    hold on
     % for idx=1:100
    bar(P1(1:30,:),'grouped')
     % end
    % title("Single-Sided Amplitude Spectrum of X(t)")
    xlabel("Order")
    ylabel("|P1(f)|")
    else 
    bx='Not Plot';
    end
end