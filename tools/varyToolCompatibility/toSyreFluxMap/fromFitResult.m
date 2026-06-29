function out = fromFitResult(FitResultStr, p, jsonPath, n0_rpm)
%FROMFITRESULT  plotMultipleInterpSatuMapSubplots 결과 → SyRE FluxMap_dq (Wrapper)
%
%   This is a backward-compatible wrapper. The robust implementation
%   is now located in the namespace package mcad.fromFitResult.
%
%   권장 워크플로우:
%     filteredTable = getMCADLabDataFromMotFile(motPath);
%     MCADLinkTable = reNameLabTable2LabLink(filteredTable);
%     FitResultStr  = plotMultipleInterpSatuMapSubplots(@plotFitResult, MCADLinkTable, 'bilinear');
%     out = fromFitResult(FitResultStr, 4, jsonPath);
%     saveSyreFluxMap(out, outMat);

if nargin < 3, jsonPath = []; end
if nargin < 4, n0_rpm   = 0;  end
out = mcad.fromFitResult(FitResultStr, p, jsonPath, n0_rpm);
end
