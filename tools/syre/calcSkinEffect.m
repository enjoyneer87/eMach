% Copyright 2020
%
%    Licensed under the Apache License, Version 2.0 (the "License");
%    you may not use this file except in compliance with the License.
%    You may obtain a copy of the License at
%
%        http://www.apache.org/licenses/LICENSE-2.0
%
%    Unless required by applicable law or agreed to in writing, software
%    distributed under the License is distributed on an "AS IS" BASIS,
%    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
%    See the License for the specific language governing permissions and
%    limitations under the License.
%
% ──────────────────────────────────────────────────────────────────────────────
% [JEET PATCH]  eMach/tools/syre/calcSkinEffect.m
%   syre_public 대비 변경:
%     'interpFreq' / 'interpFreqTemp' LUT 모드에서 범위 외 주파수 선형 외삽 추가
%     ('extrap' 옵션) → nmax 속도가 JSON 데이터 범위를 초과해도 NaN 방지
% ──────────────────────────────────────────────────────────────────────────────

function [kAC] = calcSkinEffect(skinEffectModel,freq,temp,method)

switch skinEffectModel.type
    case '0'
        kAC = 1;
    case 'interpFreq'
        if strcmp(method,'LUT')
            % [PATCH] 'extrap' 추가: 데이터 범위 밖 주파수도 선형 외삽
            kAC = interp1(skinEffectModel.f, skinEffectModel.k, freq, 'linear', 'extrap');
            kAC = max(kAC, 1);   % 물리적 제약: kAC >= 1
        else
            kAC = polyval(skinEffectModel.p,freq);
        end
    case 'interpFreqTemp'
        if strcmp(method,'LUT')
            % [PATCH] 'extrap' 추가
            kAC = interp2(skinEffectModel.f, skinEffectModel.T, skinEffectModel.k, ...
                          freq, temp.*ones(size(freq)), 'linear', 0);
            % interp2는 'extrap' 대신 기본값(0) 사용 후 수동 보정
            oob = isnan(kAC) | kAC == 0;
            if any(oob(:))
                % 범위 밖 포인트: 마지막 온도 슬라이스에서 선형 외삽
                for ii = find(oob(:))'
                    T_ii  = temp(ii);
                    f_ii  = freq(ii);
                    [~, Ti] = min(abs(skinEffectModel.T(:,1) - T_ii));
                    kAC(ii) = interp1(skinEffectModel.f(Ti,:), skinEffectModel.k(Ti,:), ...
                                      f_ii, 'linear', 'extrap');
                end
            end
            kAC = max(kAC, 1);
        else
            f = skinEffectModel.f(skinEffectModel.T==temp);
            k = skinEffectModel.k(skinEffectModel.T==temp);
            [p,~] = polyfit(f,k,7);
            kAC = polyval(p,freq);
        end
end
