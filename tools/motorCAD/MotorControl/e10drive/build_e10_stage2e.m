function build_e10_stage2e(workDir)
%BUILD_E10_STAGE2E  단계 2e — 단계 2c 모델(P.ffRef 패치 포함)을 복사해 제어기에 슬롯 고조파 대책 선택지를 넣는다.
%
%   2c/2d 모델(stage2c\e10_stage2c.slx)은 그대로 두고 stage2e\e10_stage2e.slx 를 새로 만든다.
%   선택지 (모두 0 이면 2c/2d 와 같은 제어기):
%     P.notch  측정 dq 전류에서 6차(6.4 kHz)와 접힌 12차(12.8 kHz -> 20 kHz 샘플에서 7.2 kHz)를 노치로 뺀다.
%              PI 오차와 디커플링 모두 거른 전류를 쓴다 — 조절기가 슬롯 고조파 전류를 못 보게 한다.
%     P.pr6    6차 공진(PR) 제어기로 고조파 전류를 억누른다. 위상 보상 phi = pi/2 + 1.5 w0 (지연 1.5 Ts),
%              전 샘플이 잘렸으면 공진기 입력을 0 으로 (조건부 적분).
%     P.hex    원형 클램프 대신 육각형 한계 (과변조, 방향 유지): 반지름 khex*Vdc/sqrt(3)/cos(mod(phi,60)-30).
%     P.fw     전압 피드백 약자속: 명령이 한계를 넘은 만큼 id* 를 더 깊게 (idfw += Ts(-Kfw (|v|-vlim)+ - Kleak idfw)).
%   파라미터 값은 run_e10_stage2e.m 이 16 krpm 에 맞춰 넣는다.

if nargin < 1 || isempty(workDir), workDir = 'D:\KangDH\Thesis\e10\work_lab_pc1\drive'; end
src = fullfile(workDir, 'stage2c', 'e10_stage2c.slx');
outDir = fullfile(workDir, 'stage2e');
if ~exist(outDir, 'dir'), mkdir(outDir); end
mdl = 'e10_stage2e';
dst = fullfile(outDir, [mdl '.slx']);
if bdIsLoaded(mdl), close_system(mdl, 0); end
copyfile(src, dst, 'f');
fileattrib(dst, '+w');
load_system(dst);
rt = sfroot;
charts = rt.find('-isa', 'Stateflow.EMChart');
hit = 0;
for k = 1:numel(charts)
    if strcmp(charts(k).Machine.Name, mdl) && contains(charts(k).Script, 'function [vab, dg] = ctrl')
        charts(k).Script = ctrlCode2e();
        hit = hit + 1;
    end
end
assert(hit == 1, 'expected exactly one ctrl chart in %s, found %d', mdl, hit);
mws = get_param(mdl, 'ModelWorkspace');
P = getVariable(mws, 'P');
P = defaultsE(P);
assignin(mws, 'P', P);
save_system(mdl, dst);
fprintf('model saved: %s\n', dst);
end

function P = defaultsE(P)
if ~isfield(P, 'ffRef'), P.ffRef = 0; end
P.notch = 0;  P.nb1 = [1 0 0];  P.na1 = [1 0 0];  P.nb2 = [1 0 0];  P.na2 = [1 0 0];
P.pr6 = 0;  P.prw = 0;  P.prc0 = 0;  P.prc1 = 0;  P.prKd = 0;  P.prKq = 0;
P.hex = 0;  P.khex = 0.97;
P.fw = 0;  P.Kfw = 0;  P.Kleak = 0;
end

function c = ctrlCode2e()
c = strjoin({ ...
'function [vab, dg] = ctrl(iabc, Tr, P)'
'% sim_e10_stage2 제어기 + 단계 2e 선택지 (P.notch, P.pr6, P.hex, P.fw; 모두 0 이면 2c/2d 와 같다).'
'persistent X k zn zr idfw satPrev'
'if isempty(X), X = P.X0; k = 0; zn = zeros(8,1); zr = zeros(6,1); idfw = 0; satPrev = 0; end'
't0 = k*P.Ts;  k = k + 1;'
'th0 = P.we*t0;'
'ial = (2*iabc(1) - iabc(2) - iabc(3))/3;'
'ibe = (iabc(2) - iabc(3))/sqrt(3);'
'c = cos(th0);  s = sin(th0);'
'idm =  c*ial + s*ibe;'
'iqm = -s*ial + c*ibe;'
'% (3) 노치: 6차와 접힌 12차를 되먹임 전류에서 뺀다'
'if P.notch > 0'
'    [idm, zd] = biq2(idm, zn(1:4), P.nb1, P.na1, P.nb2, P.na2);'
'    [iqm, zq] = biq2(iqm, zn(5:8), P.nb1, P.na1, P.nb2, P.na2);'
'    zn = [zd; zq];'
'end'
'Tc = min(max(Tr, 0), P.Tv(end));'
'idr = interp1(P.Tv, P.idRef, Tc) + idfw;'
'iqr = interp1(P.Tv, P.iqRef, Tc);'
'ed = idr - idm;  eq = iqr - iqm;'
'if P.ffRef > 0, idf = idr; iqf = iqr; else, idf = idm; iqf = iqm; end'
'vud = P.Kpd*ed + X(1) - P.we*P.Lq*iqf;'
'vuq = P.Kpq*eq + X(2) + P.we*(P.Ld*idf + P.lam);'
'% (3) 6차 공진 제어기 (억누르기). 앞 샘플이 잘렸으면 입력 0 (조건부 적분)'
'yd = 0;  yq = 0;'
'if P.pr6 > 0'
'    edi = ed*(1 - satPrev);  eqi = eq*(1 - satPrev);'
'    cw = 2*cos(P.prw);'
'    yd = cw*zr(1) - zr(2) + 2*P.prKd*P.Ts*(P.prc0*edi - P.prc1*zr(3));'
'    yq = cw*zr(4) - zr(5) + 2*P.prKq*P.Ts*(P.prc0*eqi - P.prc1*zr(6));'
'    zr = [yd; zr(1); edi; yq; zr(4); eqi];'
'end'
'vud = vud + yd;  vuq = vuq + yq;'
'vmag = sqrt(vud^2 + vuq^2);'
'% (4) 한계: 원 (기본) 또는 육각형 (과변조, 방향 유지)'
'if P.hex > 0'
'    ph = th0 + P.thc + atan2(vuq, vud);'
'    phm = mod(ph, pi/3) - pi/6;'
'    vlim = P.khex*P.Vdc/sqrt(3)/cos(phm);'
'else'
'    vlim = P.Vmax;'
'end'
'if vmag > vlim'
'    vsd = vud*vlim/vmag;  vsq = vuq*vlim/vmag;  sat = 1;'
'else'
'    vsd = vud;  vsq = vuq;  sat = 0;'
'end'
'satPrev = sat;'
'X(1) = X(1) + P.Ts*(P.Kid*ed + P.Kaw*(vsd - vud));'
'X(2) = X(2) + P.Ts*(P.Kiq*eq + P.Kaw*(vsq - vuq));'
'% (5) 전압 피드백 약자속: 잘린 만큼 id* 를 더 깊게, 누설로 천천히 되돌림'
'if P.fw > 0'
'    idfw = min(0, idfw + P.Ts*(-P.Kfw*max(vmag - vlim, 0) - P.Kleak*idfw));'
'end'
'cc = cos(P.thc);  sc = sin(P.thc);'
'vcd = cc*vsd - sc*vsq;  vcq = sc*vsd + cc*vsq;'
'vab = [c*vcd - s*vcq; s*vcd + c*vcq];'
'dg = [t0; idm; iqm; sqrt(vsd^2 + vsq^2); sat; idr; iqr];'
'end'
''
'function [y, z] = biq2(x, z, b1, a1, b2, a2)'
'% 두 biquad 직렬 (직접형 II 전치), z = [s1a; s2a; s1b; s2b]'
'y1 = b1(1)*x + z(1);'
'z(1) = b1(2)*x - a1(2)*y1 + z(2);'
'z(2) = b1(3)*x - a1(3)*y1;'
'y = b2(1)*y1 + z(3);'
'z(3) = b2(2)*y1 - a2(2)*y + z(4);'
'z(4) = b2(3)*y1 - a2(3)*y;'
'end'
}, newline);
end
