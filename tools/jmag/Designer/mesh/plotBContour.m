function [h, Babs_t, B] = plotBContour(msh, A, varargin)

msh=curMesh
A=curMVP*1000;
[p_plot, plotArgs] = aux_Plotting_parseInput(msh, varargin{:});
% [p_plot, plotArgs] = aux_Plotting_parseInput(msh);

%drawFluxDensity plots the flux density
%
% drawFluxDensity(msh, A, args) plots the flux density using "fill" and the
% arguments args
%
% If the mesh msh has a field "rotel" listing the rotor elements, the call 
% syntax can be drawFluxDensity(msh, A, rotorAngle, args)
% 
% Copyright (c) 2016 Antti Lehikoinen / Aalto University
% msh=curMesh
% A=curMVP
% [p_plot, plotArgs] = aux_Plotting_parseInput(msh);

[p_plot, plotArgs] = aux_Plotting_parseInput(msh, varargin{:});

if size(msh.t, 1) > 3
    % higher-order mesh
    [t, I] = aux_mesh(msh);
else
    t = msh.t;
    I = 1;
end

X = zeros(3, size(t,2));
Y = X;

for kn = 1:3
    X(kn,:) = p_plot(1, t(kn,:));
    Y(kn,:) = p_plot(2, t(kn,:));
end

%calculating flux density
[Babs_t, B] = calculate_B(A, msh);

Ne = size(msh.t,2);
Babs = zeros(size(I,1), Ne*size(I,2));
for kc = 1:size(I,2)
    Babs(:, (1:Ne) + (kc-1)*Ne) = Babs_t(I(:,kc), :);
end


%h = fill(X,Y, Babs, plotArgs{:});
h = patch(X,Y,Babs, plotArgs{:});


% 요소 중심에서의 자속 밀도 크기 추출
Babs_center = mean(Babs_t, 1);


xlabel('X (m)');
ylabel('Y (m)');