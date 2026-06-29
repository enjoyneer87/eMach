function out = fromMCAD_lab_json(motFilePath, jsonPath, p)
%FROMMCAD_LAB_JSON  Motor-CAD Lab flux linkage + JSON AC loss → SyRE FluxMap_dq (Wrapper)
%
%   This is a backward-compatible wrapper. The robust implementation
%   is now located in the namespace package mcad.fromMCAD_lab_json.

out = mcad.fromMCAD_lab_json(motFilePath, jsonPath, p);
end
