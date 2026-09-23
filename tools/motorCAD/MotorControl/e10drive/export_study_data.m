function export_study_data(workDir)
%EXPORT_STUDY_DATA  해설 페이지(drive_model_study.html) 그림용 데이터를 평범한 배열로 내보낸다.
%
%   mbc_tables.mat 의 결과는 MATLAB table 객체라 파이썬에서 읽을 수 없으므로 16 000 rpm 의
%   수렴한 TPA 해만 배열로 꺼낸다. 출력: study_data.mat (-v7)
%     id_pk, iq_pk, Fd, Fq, T_shaft (M(iq, id)), Rs, p, Vmax_pk, Vdc, we16
%     mcb_T, mcb_id, mcb_iq            MCB 기준표 (16 krpm)
%     mbc{k}_T/_id/_iq, mbc_factor     MBC calibratepmsm 수렴 해 (16 krpm, VsMax 100/95/90 %)

if nargin < 1 || isempty(workDir), workDir = 'D:\KangDH\Thesis\e10\work_lab_pc1\drive'; end
S = load(fullfile(workDir, 'e10_stage1_data_16000_shaft.mat'));
M = load(fullfile(workDir, 'mbc_tables.mat'));
o = struct();
o.id_pk = S.id_pk(:).';  o.iq_pk = S.iq_pk(:).';
o.Fd = S.Fd;  o.Fq = S.Fq;  o.T_shaft = S.T_shaft;
o.Rs = S.machine.Rs_80C;  o.p = S.machine.p;  o.Vdc = S.machine.Vdc;
o.Vmax_pk = S.machine.Vph_lim*sqrt(2);  o.we16 = S.we;
o.mcb_T = S.T_ref_vec(:).';  o.mcb_id = S.id_ref_current(:).';  o.mcb_iq = S.iq_ref_current(:).';
o.mbc_factor = [M.out.vsFactor];
for k = 1:numel(M.out)
    r = M.out(k).raw.results;
    g = sortrows(r(r.n == 16000 & r.ExitFlags > 0, :), 'Trq');
    o.(sprintf('mbc%d_T', k)) = g.Trq.';
    o.(sprintf('mbc%d_id', k)) = g.Id.';
    o.(sprintf('mbc%d_iq', k)) = g.Iq.';
end
save(fullfile(workDir, 'study_data.mat'), '-struct', 'o', '-v7');
fprintf('-> %s\n', fullfile(workDir, 'study_data.mat'));
end
