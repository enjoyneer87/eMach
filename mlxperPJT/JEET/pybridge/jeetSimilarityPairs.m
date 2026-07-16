function T = jeetSimilarityPairs(scale)
%JEETSIMILARITYPAIRS  SCL-M similarity check as a MATLAB table.
%
%   T = jeetSimilarityPairs('SC') compares each low-band operating point
%   of the scaled variant with the similarity-mapped Ref point
%   (omega -> kr^2*omega, I -> I/kr, same beta) and returns:
%       speed_rpm  irms_A  phase_deg  af_variant  af_ref_mapped  dev_pct
%
%   Example:
%       T = jeetSimilarityPairs('SC');
%       fprintf('mean |dev| = %.2f %%\n', mean(abs(T.dev_pct)));

if nargin < 1
    scale = 'SC';
end
pl = jeetGetPipeline();
d = pl.similarity_pairs(scale);

cols = {'speed_rpm', 'irms_A', 'phase_deg', ...
        'af_variant', 'af_ref_mapped', 'dev_pct'};
vals = cell(1, numel(cols));
for k = 1:numel(cols)
    vals{k} = np2mat(d.get(cols{k}));
end
T = table(vals{:}, 'VariableNames', cols);
end
