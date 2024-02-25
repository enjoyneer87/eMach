
function [BuildingData]=devExportSatuMapFromMCADLabModel(SatuMapFilePath,mcad,SaturationMap_InputDefinition,stepSize1,stepSize2)
% isBuilt=mcad.GetModelBuilt_Lab

BuildingData=getMCADBuildingData(mcad);
referenceSpeed=BuildingData.MotorCADGeo.referenceSpeed ;

%% SaturationMap Export Using Tool
SaturationMap_PhaseAdvanceMax=90;
mcad.SetVariable('SaturationMap_Export',      1);
mcad.SetVariable('LossMap_Export',            1);
mcad.SetVariable('LossMap_Speed',             referenceSpeed);

if nargin==3
    stepSize1=100;  
    % SaturationMap_InputDefinition=varargin{1};
    if SaturationMap_InputDefinition==1
    % SaturationMap_InputDefinition=1;  
    mcad.SetVariable('SaturationMap_InputDefinition',       SaturationMap_InputDefinition);
    mcad.SetVariable('SaturationMap_CalculationMethod',     0);
    mcad.SetVariable('SaturationMap_Current_D_Max',       0);
    mcad.SetVariable('SaturationMap_Current_D_Step',      Imaxpk/stepSize1);
    mcad.SetVariable('SaturationMap_Current_D_Min',       -Imaxpk);
    mcad.SetVariable('SaturationMap_Current_Q_Max',       Imaxpk);
    mcad.SetVariable('SaturationMap_Current_Q_Step',      Imaxpk/stepSize1);
    mcad.SetVariable('SaturationMap_Current_Q_Min',       0);  
    end

if nargin==5
    if SaturationMap_InputDefinition==0
    mcad.SetVariable('SaturationMap_InputDefinition',       SaturationMap_InputDefinition);
    mcad.SetVariable('SaturationMap_CalculationMethod',     0);
    mcad.SetVariable('SaturationMap_StatorCurrentMax',      Imaxpk);
    mcad.SetVariable('SaturationMap_StatorCurrentStep',     Imaxpk/stepSize1);
    mcad.SetVariable('SaturationMap_StatorCurrentMin',      0);
    mcad.SetVariable('SaturationMap_PhaseAdvanceMax',       SaturationMap_PhaseAdvanceMax);
    mcad.SetVariable('SaturationMap_PhaseAdvanceStep',      SaturationMap_PhaseAdvanceMax/stepSize2);
    mcad.SetVariable('SaturationMap_PhaseAdvanceMin',       0);
    elseif SaturationMap_InputDefinition==1;
    mcad.SetVariable('SaturationMap_InputDefinition',       SaturationMap_InputDefinition);
    mcad.SetVariable('SaturationMap_CalculationMethod',   0);
    mcad.SetVariable('SaturationMap_Current_D_Max',       0);
    mcad.SetVariable('SaturationMap_Current_D_Step',      Imaxpk/stepSize1);
    mcad.SetVariable('SaturationMap_Current_D_Min',       -Imaxpk);
    mcad.SetVariable('SaturationMap_Current_Q_Max',       Imaxpk);
    mcad.SetVariable('SaturationMap_Current_Q_Step',      Imaxpk/stepSize1);
    mcad.SetVariable('SaturationMap_Current_Q_Min',       0);
    end
end

mcad.SetVariable('SaturationMap_ExportFile',            SatuMapFilePath);

%
checkFileNMove(SatuMapFilePath)
%
    mcad.CalculateSaturationMap();

%% Exported SatuMap
satuMapData=load(SatuMapFilePath);
BuildingData.satuMapData=satuMapData;

% clear('mcad','referenceSpeed','Imax','Imaxrms','Imaxpk','ans','SpeedMax_MotorLAB')

%% reSave reFormat 
save(SatuMapFilePath,'BuildingData','-mat');

end