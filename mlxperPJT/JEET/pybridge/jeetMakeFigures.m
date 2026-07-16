function files = jeetMakeFigures(outDir)
%JEETMAKEFIGURES  Regenerate the journal validation figures (Ref, SC).
%
%   files = jeetMakeFigures()          writes into map_exports\e10\figs
%   files = jeetMakeFigures(outDir)    custom output directory
%
%   Returns a cellstr of the written PNG paths. Copy them into the
%   Overleaf fig\ folder to update the manuscript.

if nargin < 1
    outDir = ['D:\KangDH\EveryMotor\eMach\mlxperPJT\JEET' ...
              '\map_exports\e10\figs'];
end
pl = jeetGetPipeline();
outs = pl.make_all_figures(outDir);

files = cellfun(@char, cell(outs), 'UniformOutput', false);
fprintf('[jeetMakeFigures] %d figure(s) written to %s\n', ...
    numel(files), outDir);
end
