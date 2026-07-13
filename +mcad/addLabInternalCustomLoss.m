function [idx0, readback] = addLabInternalCustomLoss(mcad, name, formula, lossType, thermalNode)
%ADDLABINTERNALCUSTOMLOSS Motor-CAD Lab Internal Custom Loss 등록/교체 (ActiveX)
%
%   [idx0, readback] = mcad.addLabInternalCustomLoss(mcad, name, formula, lossType, thermalNode)
%
%   pymotorcad add_internal_custom_loss 로직의 ActiveX 미러 (0-based 인덱스):
%     NumCustomLossesInternal_Lab 증가 후 SetArrayVariable 4종
%     (Name / Function / Type / ThermalNode)_Internal_Lab
%   단, 동일 name이 이미 있으면 해당 인덱스를 덮어써 교체한다.
%
%   입력:
%     mcad        : actxserver('motorcad.appautomation') 핸들
%     name        : Custom Loss 이름 (예: 'AF_A_SC')
%     formula     : 수식 문자열 (mcad.buildAfCustomLossFormula 출력)
%     lossType    : 'Electrical' (기본) | 'Mechanical'  — Motor-CAD가 대소문자 구분
%     thermalNode : 열 노드 번호 (기본 -1 = 미지정)
%
%   출력:
%     idx0     : 등록된 0-based 인덱스
%     readback : .name/.function/.type/.thermalNode read-back 값 (검증용)
%
%   참고: 허용 변수 목록은 GetVariable('CustomLossVariablesInternal_Lab')로
%         호출 측에서 확인할 것 (runAFCustomLossLab.m S5 참조)

if nargin < 4 || isempty(lossType),    lossType = 'Electrical'; end
if nargin < 5 || isempty(thermalNode), thermalNode = -1;        end

% Motor-CAD는 Type 문자열 대소문자 구분 ('Electrical'/'Mechanical')
lossType = [upper(lossType(1)), lower(lossType(2:end))];
assert(ismember(lossType, {'Electrical', 'Mechanical'}), ...
    'lossType은 Electrical 또는 Mechanical (입력: %s)', lossType);

mcad.SetMotorLABContext();

[~, num] = mcad.GetVariable('NumCustomLossesInternal_Lab');
num = double(num);

% 동일 이름 검색 (있으면 교체)
idx0 = -1;
for i = 0:num-1
    [~, nm] = mcad.GetArrayVariable('CustomLoss_Name_Internal_Lab', i);
    if strcmpi(strtrim(char(nm)), strtrim(name))
        idx0 = i;
        fprintf('[addLabInternalCustomLoss] 기존 항목 교체: "%s" (index %d)\n', name, i);
        break
    end
end

if idx0 < 0
    mcad.SetVariable('NumCustomLossesInternal_Lab', num + 1);
    idx0 = num;
    fprintf('[addLabInternalCustomLoss] 신규 등록: "%s" (index %d)\n', name, idx0);
end

mcad.SetArrayVariable('CustomLoss_Name_Internal_Lab',        idx0, name);
mcad.SetArrayVariable('CustomLoss_Function_Internal_Lab',    idx0, formula);
mcad.SetArrayVariable('CustomLoss_Type_Internal_Lab',        idx0, lossType);
mcad.SetArrayVariable('CustomLoss_ThermalNode_Internal_Lab', idx0, thermalNode);

% read-back 검증
readback = struct();
[~, v] = mcad.GetArrayVariable('CustomLoss_Name_Internal_Lab',        idx0); readback.name        = char(v);
[~, v] = mcad.GetArrayVariable('CustomLoss_Function_Internal_Lab',    idx0); readback.function    = char(v);
[~, v] = mcad.GetArrayVariable('CustomLoss_Type_Internal_Lab',        idx0); readback.type        = char(v);
[~, v] = mcad.GetArrayVariable('CustomLoss_ThermalNode_Internal_Lab', idx0); readback.thermalNode = v;

if ~strcmp(readback.function, formula)
    warning(['read-back 수식이 입력과 다름!\n  입력(%d자): %s...\n  read-back(%d자): %s...\n' ...
             '(수식 길이 제한 또는 문법 문제 가능성)'], ...
        numel(formula), formula(1:min(80, end)), ...
        numel(readback.function), readback.function(1:min(80, end)));
else
    fprintf('[addLabInternalCustomLoss] read-back 일치 (%d자, type=%s, node=%d)\n', ...
        numel(readback.function), readback.type, readback.thermalNode);
end
end
