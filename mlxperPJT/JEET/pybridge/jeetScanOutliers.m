function T = jeetScanOutliers(scale, tol)
%JEETSCANOUTLIERS  AF neighbor-consistency scan for bad TS-FEA points.
%
%   T = jeetScanOutliers('SC')        default tolerance 0.25 (25 %)
%   T = jeetScanOutliers('SC', 0.15)  stricter
%
%   Returns a (possibly empty) table of flagged points. Points already
%   excluded by the adopted config are not re-reported.

if nargin < 2
    tol = 0.25;
end
pl = jeetGetPipeline();
flags = pl.scan_outliers(scale, tol);

n = double(py.len(flags));
cols = {'speed_rpm', 'irms_A', 'phase_deg', 'af', 'af_expected', 'dev_pct'};
data = zeros(n, numel(cols));
for i = 1:n
    f = flags{i};
    for k = 1:numel(cols)
        data(i, k) = double(f.get(cols{k}));
    end
end
T = array2table(data, 'VariableNames', cols);
end
