function filtered_signal = zeroOut3ncoeffs(signal)
% 입력 시그널의 길이 계산
n = length(signal);
% 입력 시그널의 FFT 계산
signal_fft = fft(signal);
% 3의 배수 차수에 해당하는 성분 제거
signal_fft(4) = 0;
% inverse FFT를 수행하여 filtering된 시그널 계산
filtered_signal = ifft(signal_fft);
end