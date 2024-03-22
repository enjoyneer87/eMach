function [fftMagTable,fftPhaseTable] = tableFFTwithPhase(T)
    % 테이블의 각 변수에 대해 FFT를 수행하고, 결과의 크기와 위상을 새로운 테이블로 저장하는 함수
    %
    % 입력:
    %   - T: FFT를 적용할 테이블
    %
    % 출력:
    %   - fftTable: FFT 결과의 크기와 위상을 포함하는 새로운 테이블

    % 변수 이름에 따라 크기와 위상 변수 이름을 생성하고 새 테이블을 초기화
    fftMagTable = table();
    fftPhaseTable = table();

    % 테이블의 각 변수에 대해 반복
    for varName = T.Properties.VariableNames
        % 현재 변수의 데이터 추출
        data = T.(varName{1});
        
        % 데이터가 숫자형인지 확인
        if isnumeric(data)
            % FFT 수행
            fftData = fft(data);
            
            %% Normalize
            N=length(fftData);
            Side = fftData(1:N/2);
            fftDataNormal = abs(Side)/(N/2);
            

            % FFT 결과의 크기와 위상 계산
            magnitude = abs(fftDataNormal);
            phase = angle(fftData);
            
            % 결과를 새로운 테이블에 저장
            fftMagTable.(varName{1}) = magnitude;
            fftPhaseTable.(varName{1}) = phase;
        else
            warning('Variable %s is not numeric and was skipped.', varName{1});
        end
    end
end
