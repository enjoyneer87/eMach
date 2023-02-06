function [xab, xdq] = dq_trans(x, angles)
% angles=init_angles+wt*time_step
%alpha-beta transformation (Clarke in simscape )
xab = 2/3 * [1 -0.5 -0.5; 0 sqrt(3)/2 -sqrt(3)/2]*x;
% power invariant version

%dq transformation, vectorized (Clarke to park angle transform
xdq = [cos(angles).*xab(1,:) + sin(angles).*xab(2,:);
    -sin(angles).*xab(1,:) + cos(angles).*xab(2,:)];

end