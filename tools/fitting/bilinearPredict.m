function zq = bilinearPredict(xq, yq, coeffsTable)
    zq = nan(size(xq));
    for k = 1:numel(xq)
        x = xq(k); y = yq(k);
        % 속하는 셀 찾기
        idx = find(...
            x >= coeffsTable.x1 & x <= coeffsTable.x2 & ...
            y >= coeffsTable.y1 & y <= coeffsTable.y2, 1);
        if ~isempty(idx)
            a0 = coeffsTable.a0(idx);
            a1 = coeffsTable.a1(idx);
            a2 = coeffsTable.a2(idx);
            a3 = coeffsTable.a3(idx);
            zq(k) = a0 + a1*x + a2*y + a3*x*y;
        end
    end
end