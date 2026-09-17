function ok = test_e10_plant(S)
%TEST_E10_PLANT  플랜트 단위 시험 — 제어기 없이 정상상태 전압을 열린 루프로 인가한다.
%
%   기준표의 한 점에서 정상상태 전압 vd = R id - we λq, vq = R iq + we λd 를 직접 계산해
%   그대로 인가하면 전류가 그 점에 머물러야 한다. 머물면 맵·역맵·적분이 맞다는 뜻이고,
%   폐루프가 어긋나면 원인은 제어기다.
%
%   2026-09-17 결과 (16 krpm, 20 N·m): id -217.5 대 기준 -217.6, iq 6.6 대 6.6,
%   토크 19.84 대 20.00 N·m, 필요 전압 298 V 피크 (한계 403 의 74 %) — 통과.

if nargin < 1 || isempty(S)
    S = load('D:\KangDH\Thesis\e10\work_lab_pc1\drive\e10_stage1_data_16000.mat');
end
we = S.we;  R = S.machine.Rs_80C;
ok = true;
for T = [5 20 60]
    id = interp1(S.T_ref_vec, S.id_ref_current, T);
    iq = interp1(S.T_ref_vec, S.iq_ref_current, T);
    fd = interp2(S.id_pk, S.iq_pk, S.Fd, id, iq, 'linear');
    fq = interp2(S.id_pk, S.iq_pk, S.Fq, id, iq, 'linear');
    vd = R*id - we*fq;   vq = R*iq + we*fd;

    flux = [fd; fq];  h = 2e-6;
    for k = 1:round(0.02/h)
        i1 = fluxToI(S, flux);
        flux = flux + h*[vd - R*i1(1) + we*flux(2); vq - R*i1(2) - we*flux(1)];
    end
    i2 = fluxToI(S, flux);
    Tm = interp2(S.id_pk, S.iq_pk, S.T_shaft, i2(1), i2(2), 'linear');
    e = hypot(i2(1)-id, i2(2)-iq);
    ok = ok && e < 1.0 && abs(Tm - T) < 0.05*max(T, 1);
    fprintf('T* %5.1f | 필요 전압 %5.0f V peak (한계 %.0f) | 20 ms 뒤 id %7.1f/%7.1f, iq %5.1f/%5.1f, T %6.2f | 오차 %.2f A\n', ...
            T, hypot(vd, vq), S.machine.Vph_lim*sqrt(2), i2(1), id, i2(2), iq, Tm, e);
end
fprintf('플랜트 단위 시험: %s\n', string(ok));
end

function i = fluxToI(S, flux)
i = [interp2(S.fd_vec, S.fq_vec, S.id_of_flux, flux(1), flux(2), 'linear');
     interp2(S.fd_vec, S.fq_vec, S.iq_of_flux, flux(1), flux(2), 'linear')];
end
