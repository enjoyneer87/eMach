function [fft_result] = motorcadGraphAnalysisFFT(mc_input, fmin, fmax)
    % 모터캐드 시뮬레이션을 수행하는 코드
    % 시뮬레이션 결과를 result 변수에 저장
    result = ...;
    
    % FFT 분석을 수행하여 주파수 성분 크기를 추출하는 코드
    fft_result = abs(fft(result(fmin:fmax)));
end