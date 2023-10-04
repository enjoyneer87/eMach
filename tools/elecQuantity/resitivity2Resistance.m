function R = resitivity2Resistance(length, area, resistivity)
    % length: 길이 (미터)
    % area: 단면적 (미터 제곱)
    % resistivity: 전기 저항도 (옴·미터)
    
    % 전기 저항 계산
    R = (resistivity * length) / area; 
end
