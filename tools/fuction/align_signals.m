function [shifted_signal, phase_shift] = align_signals(signal1, x1, refSginal, x2,manualAdditionalShift, interpMethod)
    % x축을 기준으로 동일한 샘플 개수를 가지도록 보간
    if nargin < 5
        interpMethod = 'linear'; % 기본 보간 방법 설정
    end

    % signal1=P_rec2DJMAG
    % x1=[0:3:360]
    % signal2=PMCADACLoss'
    % x2=[0:360/90:360]
    commonX = linspace(min(x1(1), x2(1)), max(x1(end), x2(end)), max(length(signal1), length(refSginal)));
    interpSignal1 = interp1(x1, signal1, commonX, interpMethod);
    interpSignal2 = interp1(x2, refSginal, commonX, interpMethod);
    
    % plot(commonX,interpSignal1)
    % hold on
    % plot(commonX,interpSignal2)
    % 신호의 상관 관계를 계산
    [correlation, lags] = xcorr(interpSignal1, interpSignal2);

    % 상관 관계가 최대인 지점을 찾음
    [~, maxIndex] = max(correlation);

    % 위상 차이를 계산 (최대 상관 관계를 가진 지점의 시차)
    phase_shift = lags(maxIndex);

    if nargin > 4
    phase_shift = manualAdditionalShift +  phase_shift;
    end
    % 신호의 주기 계산
    period = length(interpSignal1);

    % 위상 차이만큼 signal2를 순환 이동시킴 (반복되는 파형 고려)
    if phase_shift > 0
        shifted_signal = circshift(interpSignal1, [0, phase_shift]);
    elseif phase_shift < 0
        shifted_signal = circshift(interpSignal1, [0, phase_shift]);
    else
        shifted_signal = interpSignal1; % 위상 차이가 없을 경우
    end
end