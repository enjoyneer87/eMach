function m = jeetMetrics(scale)
%JEETMETRICS  Accuracy metrics of the adopted calibration model.
%
%   m = jeetMetrics('SC') returns a struct:
%       .mae_pct          full-map relative MAE of the calibrated model
%       .wmae_pct         loss-weighted MAE (map-level watt accuracy)
%       .hybrid_mae_pct   uncorrected Hybrid MAE
%       .hybrid_wmae_pct  uncorrected Hybrid wMAE
%       .n_points         valid TS-FEA points in the dataset
%       .n_own_samples    own TS-FEA training points of the adopted plan

pl = jeetGetPipeline();
d = pl.metrics(scale);

m = struct();
keys = cell(py.list(d.keys()));
for k = 1:numel(keys)
    name = char(keys{k});
    m.(name) = double(d.get(name));
end
end
