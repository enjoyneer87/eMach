function out = calcACLossHybridFromPDF(freqE, BrHarm, BtHarm, geom, mat, opts)
% calcACLossHybridFromPDF
% Hybrid AC copper loss estimator (harmonic-domain) prepared from PDF method notes.
%
% Inputs
%   freqE   : electrical fundamental frequency [Hz]
%   BrHarm  : radial B harmonic magnitude vector [T] (RMS or peak, keep consistent)
%   BtHarm  : tangential B harmonic magnitude vector [T]
%   geom    : struct with geometry/scale fields
%       .wCond                 conductor width [m]
%       .hCond                 conductor height [m]
%       .bundleHeight          effective bundle height [m]
%       .activeLength          active stack length [m]
%       .scaleFactor           global calibration factor (default 1)
%   mat     : struct with material fields
%       .sigma                 conductivity [S/m]
%       .mu_r                  relative permeability (default 1)
%   opts    : struct with options
%       .orderList             harmonic order list (default 1:N)
%       .useLegacyCoeff        use calcProx2DG2Prime if available (default true)
%       .includeSkinCorrection apply high-frequency correction (default true)
%       .skinDepthExp          exponent for HF gain (default 1.0)
%       .transitionSharpness   logistic transition sharpness (default 0.20)
%       .sidebandOrders        optional sideband order list (default [])
%       .sidebandGain          multiplier for sideband orders (default 1.0)
%
% Output
%   out : struct
%       .Pac_total             total AC loss estimate [W]
%       .Pac_harmonic          harmonic-wise contribution [W]
%       .freqList              harmonic frequencies [Hz]
%       .coeffiRadial          radial proximity coefficient
%       .coeffiTheta           tangential proximity coefficient
%       .alphaBlend            hybrid blend ratio (0=resistance-like, 1=inductive-like)
%       .skinDepth             skin depth per harmonic [m]
%       .fTransition           transition frequency [Hz]
%
% Notes
% - If calcProx2DG2Prime() exists in path, it is used first for compatibility.
% - Otherwise, a conservative local approximation is used.
% - Keep BrHarm/BtHarm scaling (RMS/peak) consistent with calibration data.

    validateattributes(freqE, {'numeric'}, {'scalar','positive'}, mfilename, 'freqE');
    validateattributes(BrHarm, {'numeric'}, {'vector','nonnegative'}, mfilename, 'BrHarm');
    validateattributes(BtHarm, {'numeric'}, {'vector','nonnegative'}, mfilename, 'BtHarm');

    BrHarm = BrHarm(:);
    BtHarm = BtHarm(:);
    nH = min(numel(BrHarm), numel(BtHarm));
    BrHarm = BrHarm(1:nH);
    BtHarm = BtHarm(1:nH);

    geom = fillDefaultGeom(geom);
    mat = fillDefaultMat(mat);
    opts = fillDefaultOpts(opts, nH);

    orderList = opts.orderList(:);
    if numel(orderList) ~= nH
        error('Length mismatch: orderList(%d) vs harmonics(%d).', numel(orderList), nH);
    end

    freqList = abs(freqE .* orderList);

    [coeffiRadial, coeffiTheta] = getProxCoeff(freqList, geom, mat, opts);

    if ~isempty(opts.sidebandOrders)
        isSide = ismember(orderList, opts.sidebandOrders(:));
        BrHarm(isSide) = BrHarm(isSide) .* opts.sidebandGain;
        BtHarm(isSide) = BtHarm(isSide) .* opts.sidebandGain;
    end

    baseHarm = coeffiRadial .* (BrHarm.^2) + coeffiTheta .* (BtHarm.^2);

    mu0 = 4*pi*1e-7;
    omega = 2*pi*max(freqList, 1e-9);
    skinDepth = sqrt(2 ./ (omega * mu0 * mat.mu_r * mat.sigma));

    fTransition = 2 / (2*pi*mu0*mat.mu_r*mat.sigma*geom.bundleHeight^2);
    tau = max(opts.transitionSharpness * max(fTransition, 1), 1e-9);
    alphaBlend = 1 ./ (1 + exp(-(freqList - fTransition) ./ tau));

    if opts.includeSkinCorrection
        hfGain = max(1, geom.bundleHeight ./ max(skinDepth, eps)).^opts.skinDepthExp;
    else
        hfGain = ones(size(baseHarm));
    end

    harmHybrid = (1 - alphaBlend) .* baseHarm + alphaBlend .* (baseHarm .* hfGain);

    pacPerLength = sum(harmHybrid);
    pacTotal = pacPerLength * geom.activeLength * geom.scaleFactor;

    out = struct();
    out.Pac_total = pacTotal;
    out.Pac_harmonic = harmHybrid;
    out.freqList = freqList;
    out.coeffiRadial = coeffiRadial;
    out.coeffiTheta = coeffiTheta;
    out.alphaBlend = alphaBlend;
    out.skinDepth = skinDepth;
    out.fTransition = fTransition;
end

function geom = fillDefaultGeom(geom)
    if nargin == 0 || isempty(geom)
        geom = struct();
    end
    geom = setDefault(geom, 'wCond', 3.7e-3);
    geom = setDefault(geom, 'hCond', 1.6e-3);
    geom = setDefault(geom, 'bundleHeight', geom.hCond);
    geom = setDefault(geom, 'activeLength', 0.15);
    geom = setDefault(geom, 'scaleFactor', 1.0);
end

function mat = fillDefaultMat(mat)
    if nargin == 0 || isempty(mat)
        mat = struct();
    end
    mat = setDefault(mat, 'sigma', 5.8e7);
    mat = setDefault(mat, 'mu_r', 1.0);
end

function opts = fillDefaultOpts(opts, nH)
    if nargin == 0 || isempty(opts)
        opts = struct();
    end
    opts = setDefault(opts, 'orderList', (1:nH).');
    opts = setDefault(opts, 'useLegacyCoeff', true);
    opts = setDefault(opts, 'includeSkinCorrection', true);
    opts = setDefault(opts, 'skinDepthExp', 1.0);
    opts = setDefault(opts, 'transitionSharpness', 0.20);
    opts = setDefault(opts, 'sidebandOrders', []);
    opts = setDefault(opts, 'sidebandGain', 1.0);
end

function s = setDefault(s, key, val)
    if ~isfield(s, key) || isempty(s.(key))
        s.(key) = val;
    end
end

function [cr, ct] = getProxCoeff(freqList, geom, mat, opts)
    freqList = freqList(:).';

    if opts.useLegacyCoeff && exist('calcProx2DG2Prime', 'file') == 2
        [cr, ct] = calcProx2DG2Prime([geom.wCond, geom.hCond], freqList);
        cr = cr(:);
        ct = ct(:);
        return;
    end

    % Local approximation fallback when legacy coefficient function is unavailable.
    mu0 = 4*pi*1e-7;
    omega = 2*pi*max(freqList, 1e-9);
    tauR = omega * mu0 * mat.mu_r * mat.sigma * geom.hCond^2;
    tauT = omega * mu0 * mat.mu_r * mat.sigma * geom.wCond^2;

    cr = (tauR ./ (1 + tauR)).';
    ct = (tauT ./ (1 + tauT)).';
end
