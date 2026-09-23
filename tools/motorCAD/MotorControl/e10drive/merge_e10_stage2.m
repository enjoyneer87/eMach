function out = merge_e10_stage2(workDir, nPart)
%MERGE_E10_STAGE2  run_e10_stage2(..., [i n]) 부분 결과를 stage2_results.csv, stage2_traces.mat 로 합친다.
if nargin < 1 || isempty(workDir), workDir = 'D:\KangDH\Thesis\e10\work_lab_pc1\drive'; end
res = {};  trs = {};  key = [];
for i = 1:nPart
    P = load(fullfile(workDir, sprintf('stage2_part_%d.mat', i)));
    res = [res, P.res]; trs = [trs, P.trs]; %#ok<AGROW>
    key = [key; P.mine]; %#ok<AGROW>
end
g = key(key(:, 1) == 1, 2);  [~, ig] = sort(g);
out = struct2table([res{ig}].');
writetable(out, fullfile(workDir, 'stage2_results.csv'));
t = key(key(:, 1) == 2, 2);  [~, it] = sort(t);
tr.cases = [trs{it}];
save(fullfile(workDir, 'stage2_traces.mat'), '-struct', 'tr', '-v7');
fprintf('-> %d 행, 파형 %d 건\n', height(out), numel(tr.cases));
end
