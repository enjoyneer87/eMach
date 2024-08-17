function Bk_magnitude = calcMagBk(B1, B2, k,B3)
    % B_k의 크기 계산
    if nargin<3
    Bk_magnitude_k = sqrt(abs(B1).^2 + abs(B2.^2 ));
    else
    Bk_magnitude_k = sqrt(abs(B1(k)).^2 + abs(B2(k)).^2 + abs(B3(k)).^2);
    end
    % 결과 반환
    Bk_magnitude = Bk_magnitude_k;
end
