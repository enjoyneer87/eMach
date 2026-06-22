function hFig = interactiveMESFieldSlider(mesPath, varargin)
% interactiveMESFieldSlider
% MATLAB uicontrol-based step slider viewer for .mes/.txt/.h5 field data.
%
% This viewer uses loadMESviaPythonForMATLAB() and its cache path.
% First load can take time, then step changes reuse cached txt when available.
%
% Example:
%   mesPath = "F:\KDH\Thesis\JEET\e10\refModel\e10_UserRemesh\FEResultsData\OnLoadTorque_result_1.mes";
%   motPath = "F:\KDH\Thesis\JEET\e10\refModel\e10_UserRemesh.mot";
%   interactiveMESFieldSlider(mesPath, 'MotPath', motPath, 'UseCache', true);
%
% Name-Value:
%   MotPath       : optional .mot path for first export fallback
%   UseCache      : true/false (default: true)
%   FirstStep     : export first step (default: 1)
%   FinalStep     : export final step (default: 45)
%   InitialField  : 'Bx' | 'By' | '|B|' | 'A' | 'J' (default: '|B|')
%   InitialMode   : 'mesh' | 'scatter' | 'quiver' (default: 'mesh')
%   QuiverStride  : element decimation stride for quiver (default: 20)

    p = inputParser;
    addRequired(p, 'mesPath', @(x) ischar(x) || isstring(x));
    addParameter(p, 'MotPath', "", @(x) ischar(x) || isstring(x));
    addParameter(p, 'UseCache', true, @(x) islogical(x) || isnumeric(x));
    addParameter(p, 'FirstStep', 1, @(x) isnumeric(x) && isscalar(x));
    addParameter(p, 'FinalStep', 45, @(x) isnumeric(x) && isscalar(x));
    addParameter(p, 'InitialField', '|B|', @(x) ischar(x) || isstring(x));
    addParameter(p, 'InitialMode', 'mesh', @(x) ischar(x) || isstring(x));
    addParameter(p, 'QuiverStride', 20, @(x) isnumeric(x) && isscalar(x) && x >= 1);
    parse(p, mesPath, varargin{:});

    mesPath = string(p.Results.mesPath);
    motPath = string(p.Results.MotPath);
    useCache = logical(p.Results.UseCache);
    firstStep = double(p.Results.FirstStep);
    finalStep = double(p.Results.FinalStep);
    activeUseCache = useCache;

    state = struct();
    state.mesPath = mesPath;
    state.motPath = motPath;
    state.useCache = useCache;
    state.firstStep = firstStep;
    state.finalStep = finalStep;
    state.quiverStride = max(1, round(p.Results.QuiverStride));

    state.fieldOptions = {'Bx','By','|B|','A','J'};
    state.modeOptions = {'mesh','scatter','quiver'};

    initField = char(p.Results.InitialField);
    initMode = lower(string(p.Results.InitialMode));

    if ~ismember(initField, state.fieldOptions)
        initField = '|B|';
    end
    if ~ismember(char(initMode), state.modeOptions)
        initMode = 'mesh';
    end

    state.curField = initField;
    state.curMode = char(initMode);

    D0 = localLoadAtStep([], activeUseCache);
    if activeUseCache && firstStep < finalStep
        n0 = numel(double(D0.StepKeys(:)));
        if n0 <= 1
            % Guard against stale single-step cache file: probe once without cache.
            Dprobe = localLoadAtStep([], false);
            nProbe = numel(double(Dprobe.StepKeys(:)));
            if nProbe > 1
                D0 = Dprobe;
                activeUseCache = false;
            end
        end
    end
    if isempty(D0.StepKeys)
        state.stepKeys = D0.UsedStep;
    else
        state.stepKeys = D0.StepKeys(:)';
    end
    state.stepIndex = 1;
    state.D = D0;

    hFig = figure('Name', 'MES Field Viewer (Slider)', 'Color', 'w', 'Position', [80, 80, 1280, 760]);
    state.ax = axes('Parent', hFig, 'Position', [0.06, 0.13, 0.68, 0.8]);

    nSteps = numel(state.stepKeys);
    maxVal = max(1, nSteps);
    sliderStep = [1/max(maxVal-1,1), min(10/max(maxVal-1,1), 1)];

    state.hStepSlider = uicontrol(hFig, 'Style', 'slider', ...
        'Min', 1, 'Max', maxVal, 'Value', 1, ...
        'SliderStep', sliderStep, ...
        'Units', 'normalized', 'Position', [0.06, 0.04, 0.68, 0.04], ...
        'Callback', @onStepChanged);

    state.hStepLabel = uicontrol(hFig, 'Style', 'text', ...
        'String', '', 'HorizontalAlignment', 'left', ...
        'BackgroundColor', 'w', ...
        'Units', 'normalized', 'Position', [0.06, 0.0, 0.68, 0.03]);

    state.hFieldPopup = uicontrol(hFig, 'Style', 'popupmenu', ...
        'String', state.fieldOptions, ...
        'Value', find(strcmp(state.fieldOptions, state.curField), 1), ...
        'Units', 'normalized', 'Position', [0.78, 0.86, 0.18, 0.05], ...
        'Callback', @onFieldChanged);

    state.hModePopup = uicontrol(hFig, 'Style', 'popupmenu', ...
        'String', state.modeOptions, ...
        'Value', find(strcmp(state.modeOptions, state.curMode), 1), ...
        'Units', 'normalized', 'Position', [0.78, 0.79, 0.18, 0.05], ...
        'Callback', @onModeChanged);

    state.hMeshChk = uicontrol(hFig, 'Style', 'checkbox', ...
        'String', 'Mesh Overlay', 'Value', 0, ...
        'BackgroundColor', 'w', ...
        'Units', 'normalized', 'Position', [0.78, 0.73, 0.18, 0.04], ...
        'Callback', @onOptionChanged);

    state.hInfo = uicontrol(hFig, 'Style', 'text', ...
        'String', '', ...
        'HorizontalAlignment', 'left', ...
        'BackgroundColor', 'w', ...
        'Units', 'normalized', 'Position', [0.78, 0.12, 0.20, 0.58]);

    guidata(hFig, state);
    localRender();

    function D = localLoadAtStep(stepKey, useCacheFlag)
        args = {'UseCache', logical(useCacheFlag), 'FirstStep', firstStep, 'FinalStep', finalStep};
        if strlength(strtrim(motPath)) > 0
            args = [args, {'MotPath', char(motPath)}];
        end
        if ~isempty(stepKey)
            args = [args, {'StepKey', double(stepKey)}];
        end
        D = loadMESviaPythonForMATLAB(mesPath, args{:});
    end

    function onStepChanged(src, ~)
        st = guidata(src);
        idx = round(get(st.hStepSlider, 'Value'));
        idx = min(max(1, idx), numel(st.stepKeys));
        set(st.hStepSlider, 'Value', idx);
        st.stepIndex = idx;

        stepKey = st.stepKeys(idx);
        st.D = localLoadAtStep(stepKey, activeUseCache);

        guidata(hFig, st);
        localRender();
    end

    function onFieldChanged(src, ~)
        st = guidata(src);
        i = get(st.hFieldPopup, 'Value');
        st.curField = st.fieldOptions{i};
        guidata(hFig, st);
        localRender();
    end

    function onModeChanged(src, ~)
        st = guidata(src);
        i = get(st.hModePopup, 'Value');
        st.curMode = st.modeOptions{i};
        guidata(hFig, st);
        localRender();
    end

    function onOptionChanged(~, ~)
        localRender();
    end

    function localRender()
        st = guidata(hFig);
        D = st.D;

        X = D.NodeXYmm(:,1);
        Y = D.NodeXYmm(:,2);
        tri = [D.Elements.Node1, D.Elements.Node2, D.Elements.Node3];

        bx = D.Bx;
        by = D.By;
        bmag = sqrt(bx.^2 + by.^2);

        switch st.curField
            case 'Bx'
                val = bx;
                fieldLabel = 'Bx [T]';
            case 'By'
                val = by;
                fieldLabel = 'By [T]';
            case '|B|'
                val = bmag;
                fieldLabel = '|B| [T]';
            case 'A'
                val = D.A;
                fieldLabel = 'A';
            case 'J'
                val = D.J;
                fieldLabel = 'J';
            otherwise
                val = bmag;
                fieldLabel = '|B| [T]';
        end

        xc = (X(tri(:,1)) + X(tri(:,2)) + X(tri(:,3))) / 3;
        yc = (Y(tri(:,1)) + Y(tri(:,2)) + Y(tri(:,3))) / 3;

        cla(st.ax);
        axes(st.ax);

        switch st.curMode
            case 'mesh'
                patch('Faces', tri, 'Vertices', [X Y], ...
                    'FaceVertexCData', val, ...
                    'FaceColor', 'flat', ...
                    'EdgeColor', [0.7 0.7 0.7], ...
                    'LineWidth', 0.15, ...
                    'Parent', st.ax);
                colorbar(st.ax);
                if get(st.hMeshChk, 'Value')
                    hold(st.ax, 'on');
                    triplot(tri, X, Y, 'k-', 'LineWidth', 0.1, 'Color', [0 0 0 0.18]);
                    hold(st.ax, 'off');
                end

            case 'scatter'
                scatter(st.ax, xc, yc, 8, val, 'filled');
                colorbar(st.ax);
                if get(st.hMeshChk, 'Value')
                    hold(st.ax, 'on');
                    triplot(tri, X, Y, 'k-', 'LineWidth', 0.1, 'Color', [0 0 0 0.18]);
                    hold(st.ax, 'off');
                end

            case 'quiver'
                idx = 1:st.quiverStride:numel(xc);
                hPlot = quiver(st.ax, xc(idx), yc(idx), bx(idx), by(idx), 0.8, 'k'); %#ok<NASGU>
                fieldLabel = 'B vector (Bx, By)';
                if get(st.hMeshChk, 'Value')
                    hold(st.ax, 'on');
                    triplot(tri, X, Y, 'k-', 'LineWidth', 0.1, 'Color', [0 0 0 0.18]);
                    hold(st.ax, 'off');
                end

            otherwise
                hPlot = scatter(st.ax, xc, yc, 8, val, 'filled'); %#ok<NASGU>
                colorbar(st.ax);
        end

        axis(st.ax, 'equal');
        grid(st.ax, 'on');
        xlabel(st.ax, 'X [mm]');
        ylabel(st.ax, 'Y [mm]');

        stepKey = st.stepKeys(st.stepIndex);
        title(st.ax, sprintf('Step %d | %s | mode=%s', stepKey, fieldLabel, st.curMode));

        set(st.hStepLabel, 'String', sprintf('Step %d / %d (stepKey=%d)', st.stepIndex, numel(st.stepKeys), stepKey));

        infoText = {
            sprintf('SourceMode: %s', string(D.SourceMode))
            sprintf('UsedCache: %d', logical(D.UsedCache))
            sprintf('Elements: %d', height(D.Elements))
            sprintf('Nodes: %d', height(D.Nodes))
            sprintf('CacheTxt: %s', string(D.CacheTxtPath))
        };
        set(st.hInfo, 'String', infoText);
    end
end
