function acLF = buildAcLossFactor(FluxMap_dq, Rs0, tempCu, l, lend, p_pairs)
%MCAD.BUILDACLOSS FACTOR  FluxMap_dq AC 손실 데이터 → SyRE acLossFactor 구조체 변환
%
%   acLF = mcad.buildAcLossFactor(FluxMap_dq, Rs0, tempCu, l, lend, p_pairs)
%
%   SyRE calcSkinEffect 요구 포맷:
%       acLF.type = 'interpFreq'
%       acLF.f    = [0, f1, f2, ...] (Hz)  ← 전기 주파수, 반드시 0 포함
%       acLF.k    = [1, k1, k2, ...]       ← kAC (Rac_slot / Rdc_slot)
%       acLF.p    = polyfit 계수 (7차)
%       acLF.s, acLF.n
%
%   kAC 정의 (SyRE calcRsTempFreq 기준):
%       Rs = R20 * (kAC*l/(l+lend) + lend/(l+lend)) * (1+0.004*(T-20))
%       Pac_syre = 3/2 * R20 * (kAC-1) * l/(l+lend) * Is^2
%       → kAC = 1 + Pac_total_W / (3/2 * R20 * l/(l+lend) * Is^2)
%
%   근사 방법: 각 속도에서 Is^2 가중 평균으로 대표 kAC 산출
%              (근접 효과가 Is^2에 비례하지 않는 부분은 근사임)
%
%   Inputs
%   ------
%   FluxMap_dq : mcad.fromFitResult 결과 구조체 (Pac_total_kW 필드 포함)
%   Rs0        : DC 저항 at tempCu (Ohm/phase)
%   tempCu     : 기준 온도 (°C)
%   l          : 활성 스택 길이 (m)
%   lend       : 엔드와인딩 길이 (m)
%   p_pairs    : 극쌍수

%% 유효성 검사
if ~isfield(FluxMap_dq, 'Pac_total_kW') || ~isfield(FluxMap_dq, 'speed_vec')
    warning('mcad:buildAcLossFactor:noData', ...
        'FluxMap_dq에 Pac_total_kW 또는 speed_vec 필드가 없습니다. acLossFactor = []');
    acLF = [];
    return;
end

%% 기본 파라미터
R20    = Rs0 / (1 + 0.004*(tempCu - 20));   % 20°C 기준 저항
l_frac = l / (l + lend);                     % 활성 권선 비율

Id_rms    = FluxMap_dq.Id;           % [A RMS]  (nIq × nId)
Iq_rms    = FluxMap_dq.Iq;           % [A RMS]
Pac_3d    = FluxMap_dq.Pac_total_kW; % [kW]     (nIq × nId × nS)
speed_vec = FluxMap_dq.speed_vec;    % [rpm]    (1 × nS)
nS        = numel(speed_vec);

Is_rms = sqrt(Id_rms.^2 + Iq_rms.^2);   % 전류 크기 (nIq × nId)

%% 각 속도에서 kAC 산출
kAC_vec = zeros(1, nS);

for k = 1:nS
    Pac_2d = Pac_3d(:,:,k) * 1000;   % kW → W (3상 합계)

    % 유효 포인트: Is > 5 A RMS, Pac > 0 W
    valid = Is_rms > 5 & Pac_2d > 0;

    if sum(valid(:)) < 3
        kAC_vec(k) = 1;
        fprintf('  buildAcLossFactor: speed=%.0f rpm → 유효 포인트 부족, kAC=1 설정\n', speed_vec(k));
        continue;
    end

    Is_v  = Is_rms(valid);
    Pac_v = Pac_2d(valid);

    % kAC at each valid (Id, Iq) point
    %   kAC_i = 1 + Pac_i / (3/2 * R20 * l_frac * Is_i^2)
    Pj_dc_slot = 1.5 * R20 * l_frac * Is_v.^2;   % SyRE 기준 DC 슬롯 동손
    kAC_pts = 1 + Pac_v ./ max(Pj_dc_slot, 1e-10);
    kAC_pts = max(kAC_pts, 1.0);   % 물리적 제약: kAC ≥ 1

    % Is^2 가중 평균 (고전류 운전점에 더 많은 가중치)
    w = Is_v.^2;
    kAC_vec(k) = sum(kAC_pts .* w) / sum(w);
end

%% 전기 주파수 벡터 (Hz)
freq_Hz = speed_vec * p_pairs / 60;

% f=0 점 추가 (DC: kAC=1, AC 손실 없음)
if freq_Hz(1) > 0
    freq_Hz = [0,  freq_Hz];
    kAC_vec = [1, kAC_vec];
end

%% 다항식 피팅 (polyfit — 'poly' method용; 'LUT'은 f/k 직접 사용)
n_poly = min(7, numel(freq_Hz) - 1);
if n_poly >= 1
    [p_poly, s_poly] = polyfit(freq_Hz, kAC_vec, n_poly);
else
    p_poly = [0, 1];   % 상수 kAC=1
    s_poly = [];
end

%% 출력 구조체 조립
acLF.type = 'interpFreq';
acLF.f    = freq_Hz;
acLF.k    = kAC_vec;
acLF.p    = p_poly;
acLF.s    = s_poly;
acLF.n    = n_poly;

%% 요약 출력
fprintf('  buildAcLossFactor: %d 속도 포인트, kAC 범위 %.3f – %.3f\n', ...
    nS, min(kAC_vec), max(kAC_vec));
fprintf('  f [Hz]: ');
fprintf('%.0f ', freq_Hz);
fprintf('\n  k []:   ');
fprintf('%.3f ', kAC_vec);
fprintf('\n');
end
