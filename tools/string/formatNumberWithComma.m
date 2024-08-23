function formattedStr = formatNumberWithComma(num)
    % 이 함수는 숫자를 쉼표로 구분된 문자열로 변환합니다.
    formattedStr = regexprep(sprintf('%.0f', num), '(\d)(?=(\d{3})+(?!\d))', '$1,');
end