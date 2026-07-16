function G = jeetTransferAblation(scale, nBaseList, nSpd8List, nSeeds)
%JEETTRANSFERABLATION  wMAE grid of the transfer-based sampling plan.
%
%   G = jeetTransferAblation('SC') returns a struct:
%       .n_base    tested 16-kRPM base-point counts (rows)
%       .n_spd8    tested own 8-kRPM calibration counts (cols)
%       .wmae_pct  [numel(n_base) x numel(n_spd8)] mean wMAE grid
%
%   Optional: jeetTransferAblation('SC', [8 12 16 24], 0:4, 10)
%
%   Example (heatmap in MATLAB):
%       G = jeetTransferAblation('SC');
%       heatmap(G.n_spd8, G.n_base, G.wmae_pct);

pl = jeetGetPipeline();
args = {scale};
if nargin >= 2 && ~isempty(nBaseList)
    args{end+1} = py.list(int32(nBaseList));    %#ok<*AGROW>
else
    args{end+1} = py.None;
end
if nargin >= 3 && ~isempty(nSpd8List)
    args{end+1} = py.list(int32(nSpd8List));
else
    args{end+1} = py.None;
end
if nargin >= 4
    args{end+1} = int32(nSeeds);
end

d = pl.transfer_ablation_grid(args{:});
G = struct();
G.n_base = np2mat(d.get('n_base'));
G.n_spd8 = np2mat(d.get('n_spd8'));
G.wmae_pct = np2mat(d.get('wmae_pct'));
end
