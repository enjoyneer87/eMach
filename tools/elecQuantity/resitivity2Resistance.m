function R = resitivity2Resistance(TotallengthofSingleCoil, SingleCoilarea, resistivity)
    % length: 길이 (미터)
    % area: 단면적 (미터 제곱)
    % resistivity: 전기 저항도 (옴·미터)
    if nargin<3
    resistivity=1.724e-8;
    % 1.8595064E-8
    end
    % 전기 저항 계산
    R = (resistivity * TotallengthofSingleCoil) / SingleCoilarea; 
end
