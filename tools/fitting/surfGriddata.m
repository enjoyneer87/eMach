function surfGriddata(x,y,values)

 % 삼각형 메쉬 내의 더 조밀한 그리드 생성
    [Xq, Yq] = meshgrid(linspace(min(x), max(x), 100), linspace(min(y), max(y), 100));
    
    % 물리량을 보간 (interpolation)
    interpolatedValues = griddata(x, y, values, Xq, Yq, 'cubic');
    surf(Xq,Yq,interpolatedValues,'EdgeColor','none');
end