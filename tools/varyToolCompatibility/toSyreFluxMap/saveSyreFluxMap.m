function saveSyreFluxMap(out, matPath, motorModelPath)
%SAVESYREFLUXMAP  fromMCAD_lab_json 결과를 SyRE MMM 호환 .mat으로 저장 (Wrapper)
%
%   This is a backward-compatible wrapper. The robust implementation
%   is now located in the namespace package mcad.saveSyreFluxMap.

if nargin < 3, motorModelPath = []; end
mcad.saveSyreFluxMap(out, matPath, motorModelPath);
end
