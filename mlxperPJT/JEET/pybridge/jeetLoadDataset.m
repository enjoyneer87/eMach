function ds = jeetLoadDataset(scale)
%JEETLOADDATASET  Load a TS-FEA/Hybrid AF dataset into the workspace.
%
%   ds = jeetLoadDataset('SC') returns a struct with column vectors:
%       .speed_rpm  .irms_A  .phase_deg  .af  .hybrid_kW  .tsfea_kW
%   Data-quality exclusions of the adopted config are already applied.
%
%   Example:
%       ds = jeetLoadDataset('SC');
%       scatter3(ds.irms_A, ds.phase_deg, ds.af, 20, ds.speed_rpm, 'filled')

pl = jeetGetPipeline();
d = pl.dataset_struct(scale);

ds = struct();
keys = {'speed_rpm', 'irms_A', 'phase_deg', 'af', 'hybrid_kW', 'tsfea_kW'};
for k = 1:numel(keys)
    ds.(keys{k}) = np2mat(d.get(keys{k}));
end
end
