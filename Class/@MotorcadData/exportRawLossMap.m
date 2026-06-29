function inputobj = exportRawLossMap(inputobj)
%From MotorCAD Lab Calculation extract the SaturationModel of 30 Point
% inputobj = MotorcadData  obj
% 
% Refactored as a hybrid method:
% 1. Direct offline .mot text parsing (fast, cross-platform)
% 2. COM/ActiveX Fallback on Windows (failsafe)

% Initialize fields
inputobj.LossParameters_MotorLAB = [];
inputobj.ModelParameters_MotorLAB = [];

inputobj.LossParameters_MotorLAB.RawLossMap.LossModel_Is_Lab = [];
inputobj.LossParameters_MotorLAB.RawLossMap.LossModel_Gamma_Lab = [];
inputobj.LossParameters_MotorLAB.RawLossMap.FeHysLossArray_MotorLAB = [];
inputobj.LossParameters_MotorLAB.RawLossMap.FeLossBackIronHy_MotorLAB = [];
inputobj.LossParameters_MotorLAB.RawLossMap.FeLossToothHy_MotorLAB = [];
inputobj.LossParameters_MotorLAB.RawLossMap.FeLossRotorPoleHy_MotorLAB = [];
inputobj.LossParameters_MotorLAB.RawLossMap.FeLossRotorHy_MotorLAB = [];
inputobj.LossParameters_MotorLAB.RawLossMap.FeEddyLossArray_MotorLAB = [];
inputobj.LossParameters_MotorLAB.RawLossMap.FeLossBackIronEd_MotorLAB = [];
inputobj.LossParameters_MotorLAB.RawLossMap.FeLossToothEd_MotorLAB = [];
inputobj.LossParameters_MotorLAB.RawLossMap.FeLossRotorEd_MotorLAB = [];
inputobj.LossParameters_MotorLAB.RawLossMap.FeLossRotorPoleEd_MotorLAB = [];
inputobj.LossParameters_MotorLAB.RawLossMap.MagLossArray_MotorLAB = [];
inputobj.LossParameters_MotorLAB.RawLossMap.FEALossMap_RefSpeed_Lab = [];

inputobj.LossParameters_MotorLAB.FeLossUnit = '[Watts]';
inputobj.ModelParameters_MotorLAB.RawLossMap.LossModel_AC_Lab = [];

FieldsNamesLossModelLAB = fieldnames(inputobj.LossParameters_MotorLAB.RawLossMap);

proj = strcat(inputobj.file_path, '\', inputobj.file_name, '.mot');

% Try Direct Parse first
successDirect = false;
try
    if isfile(proj)
        fprintf('  [exportRawLossMap] Trying direct text parsing of %s...\n', proj);
        axStruct = getMcadActiveXTableFromMotFile(proj);
        
        ModelBuildPoints_Current_Lab = getVarFromActiveXStruct(axStruct, 'ModelBuildPoints_Current_Lab');
        ModelBuildPoints_Gamma_Lab = getVarFromActiveXStruct(axStruct, 'ModelBuildPoints_Gamma_Lab');
        FEALossMap_RefSpeed_Lab = getVarFromActiveXStruct(axStruct, 'FEALossMap_RefSpeed_Lab');
        
        if ~isempty(ModelBuildPoints_Current_Lab) && ~isempty(ModelBuildPoints_Gamma_Lab)
            NcurrentVec = ModelBuildPoints_Current_Lab;
            NphaseVec = ModelBuildPoints_Gamma_Lab;
            inputobj.LossParameters_MotorLAB.RawLossMap.FEALossMap_RefSpeed_Lab = FEALossMap_RefSpeed_Lab;
            
            % Read all variables from struct
            parsed_all = true;
            for fieldIndex = 1:(length(FieldsNamesLossModelLAB)-1)
                varName = FieldsNamesLossModelLAB{fieldIndex};
                val = getVarFromActiveXStruct(axStruct, varName);
                if ~isempty(val)
                    inputobj.LossParameters_MotorLAB.RawLossMap.(varName) = (reshape(val, [NphaseVec, NcurrentVec]))';
                else
                    % Check if the field is critical.
                    if strcmp(varName, 'LossModel_Is_Lab') || strcmp(varName, 'LossModel_Gamma_Lab')
                        parsed_all = false;
                        break;
                    end
                end
            end
            
            if parsed_all
                successDirect = true;
                fprintf('  [exportRawLossMap] Direct text parsing completed successfully.\n');
            end
        end
    end
catch ME
    fprintf('  [exportRawLossMap] Direct parsing failed: %s\n', ME.message);
end

% Fallback to ActiveX/COM if direct parse failed
if ~successDirect
    if ispc
        fprintf('  [exportRawLossMap] Direct parsing failed. Launching Motor-CAD COM Fallback...\n');
        try
            mcad = actxserver('MotorCAD.AppAutomation');
            invoke(mcad, 'LoadFromFile', proj);
            
            [~, cur_val] = invoke(mcad, 'GetVariable', 'ModelBuildPoints_Current_Lab');
            [~, gam_val] = invoke(mcad, 'GetVariable', 'ModelBuildPoints_Gamma_Lab');
            [~, speed_val] = invoke(mcad, 'GetVariable', 'FEALossMap_RefSpeed_Lab');
            
            NcurrentVec = cur_val; if ischar(NcurrentVec) || isstring(NcurrentVec), NcurrentVec = str2double(NcurrentVec); end
            NphaseVec = gam_val; if ischar(NphaseVec) || isstring(NphaseVec), NphaseVec = str2double(NphaseVec); end
            FEALossMap_RefSpeed_Lab = speed_val; if ischar(FEALossMap_RefSpeed_Lab) || isstring(FEALossMap_RefSpeed_Lab), FEALossMap_RefSpeed_Lab = str2double(FEALossMap_RefSpeed_Lab); end
            
            inputobj.LossParameters_MotorLAB.RawLossMap.FEALossMap_RefSpeed_Lab = FEALossMap_RefSpeed_Lab;
            
            for fieldIndex = 1:(length(FieldsNamesLossModelLAB)-1)
                varName = FieldsNamesLossModelLAB{fieldIndex};
                [~, charTypeData] = invoke(mcad, 'GetVariable', varName);
                val = parseNumericString(charTypeData);
                if ~isempty(val)
                    inputobj.LossParameters_MotorLAB.RawLossMap.(varName) = (reshape(val, [NphaseVec, NcurrentVec]))';
                end
            end
            
            invoke(mcad, 'Quit');
            fprintf('  [exportRawLossMap] COM Fallback completed successfully.\n');
        catch ME_fallback
            try invoke(mcad, 'Quit'); catch, end
            error('COM Fallback also failed: %s\nDetails: %s', ME_fallback.identifier, ME_fallback.message);
        end
    else
        error('[exportRawLossMap] Direct parsing failed and COM Fallback is not supported on this OS.');
    end
end
end

function val = getVarFromActiveXStruct(axStruct, varName)
val = [];
tableNames = fieldnames(axStruct);
for tIdx = 1:numel(tableNames)
    tableName = tableNames{tIdx};
    tbl = axStruct.(tableName);
    idx = find(strcmp(tbl.AutomationName, varName), 1);
    if ~isempty(idx)
        valStr = tbl.CurrentValue{idx};
        if iscell(valStr) && ~isempty(valStr)
            valStr = valStr{1};
        end
        if ischar(valStr) || isstring(valStr)
            val = parseNumericString(valStr);
            if isempty(val)
                val = str2double(valStr);
                if isnan(val)
                    val = valStr;
                end
            end
        else
            val = valStr;
        end
        return;
    end
end
end

function nums = parseNumericString(s)
s = strrep(s, ':', ' ');
s = strrep(s, ';', ' ');
nums = sscanf(s, '%f');
end


