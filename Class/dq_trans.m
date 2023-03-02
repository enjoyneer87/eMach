function [xab0, xdq] = dq_trans(x, angles)
% angles=init_angles+wt*time_step
%alpha-beta transformation (Clarke in simscape )
xab0 = 2/3 * [1 -0.5 -0.5; 0 sqrt(3)/2 -sqrt(3)/2; 1/2 1/2 1/2]*x;
% power invariant version

%dq transformation, vectorized (Clarke to park angle transform
xdq = [cos(angles).*xab0(1,:) + sin(angles).*xab0(2,:);
    -sin(angles).*xab0(1,:) + cos(angles).*xab0(2,:)];

end