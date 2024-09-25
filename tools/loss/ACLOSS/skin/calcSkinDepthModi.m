function [delta_prime,delta] = calcSkinDepthModi(dim1,dividerDim2,freqE)
% dim1=dx
% dividerDim2=dy
            delta         =mm2m(calcSkinDepth(freqE));           % 스킨 깊이 [m]
            delta_prime = delta .* sqrt((dim1 + dividerDim2) / (2 * dividerDim2));    % w' > 나누기 2h
end