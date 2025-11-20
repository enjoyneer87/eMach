classdef BasisModel
    properties
        mode (1, :) char {mustBeMember(mode, {'polynomial','rbf','chebyshev','legendre','thinplate','tpaps'})} = 'polynomial';
        degree (1,1) double {mustBeInteger, mustBePositive} = 3;
        coeff
        scaler % [mu; sigma]
        centers % for rbf/thinplate
        tpapsFn % for 'tpaps' mode
        tpapsP % smoothing parameter (for 'tpaps')
        maskConvexHull (1,1) logical = false;
        hull % convex hull vertices for masking
    end

    methods
        function obj = BasisModel(mode, degree)
            if nargin >= 1
                obj.mode = mode;
            end
            if nargin >= 2
                obj.degree = degree;
            end
        end

        function obj = fit(obj, x, y, z)
            [xNorm, yNorm, mu, sigma] = normalize2d(x, y);
            obj.scaler = [mu; sigma];

            if obj.maskConvexHull
                K = convhull(x, y);
                obj.hull = [x(K), y(K)];
            end

            switch obj.mode
                case 'polynomial'
                    Phi = createPolyBasis(xNorm, yNorm, obj.degree);
                    obj.coeff = Phi \ z;
                case 'rbf'
                    [Phi, centers] = createRBFBasis(xNorm, yNorm, obj.degree);
                    obj.centers = centers;
                    obj.coeff = Phi \ z;
                case 'chebyshev'
                    Phi = createChebyshevBasis(xNorm, yNorm, obj.degree);
                    obj.coeff = Phi \ z;
                case 'legendre'
                    Phi = createLegendreBasis(xNorm, yNorm, obj.degree);
                    obj.coeff = Phi \ z;
                case 'thinplate'
                    [Phi, centers] = createThinPlateBasis(xNorm, yNorm, obj.degree);
                    obj.centers = centers;
                    obj.coeff = Phi \ z;
                case 'tpaps'
                    [~, ~, mu, sigma] = normalize2d(x, y);
                    obj.scaler = [mu; sigma];
                    xy = [xNorm'; yNorm'];
                    obj.tpapsP = obj.degree; % reinterpret degree as smoothing p
                    obj.tpapsFn = tpaps(xy, z', obj.tpapsP);
                otherwise
                    error('지원되지 않는 basis 모드입니다.');
            end
        end

        function zhat = evaluate(obj, x, y)
            x = x(:);
            y = y(:);
            mu = obj.scaler(1, :);
            sigma = obj.scaler(2, :);
            xNorm = (x - mu(1)) ./ sigma(1);
            yNorm = (y - mu(2)) ./ sigma(2);

            switch obj.mode
                case 'polynomial'
                    Phi = createPolyBasis(xNorm, yNorm, obj.degree);
                    zhat = Phi * obj.coeff;
                case 'rbf'
                    Phi = createRBFBasis(xNorm, yNorm, obj.degree, obj.centers);
                    zhat = Phi * obj.coeff;
                case 'chebyshev'
                    Phi = createChebyshevBasis(xNorm, yNorm, obj.degree);
                    zhat = Phi * obj.coeff;
                case 'legendre'
                    Phi = createLegendreBasis(xNorm, yNorm, obj.degree);
                    zhat = Phi * obj.coeff;
                case 'thinplate'
                    Phi = createThinPlateBasis(xNorm, yNorm, obj.degree, obj.centers);
                    zhat = Phi * obj.coeff;
                case 'tpaps'
                    zhat = fnval(obj.tpapsFn, [xNorm'; yNorm']);
                    zhat = zhat(:);
                otherwise
                    error('지원되지 않는 basis 모드입니다.');
            end

            if obj.maskConvexHull && ~isempty(obj.hull)
                in = inpolygon(x, y, obj.hull(:,1), obj.hull(:,2));
                zhat(~in) = NaN;
            end
        end

        function [bestModel, bestRMSE] = fitBestDegree(obj, x, y, z, degreeRange, rmseThreshold)
            bestRMSE = inf;
            bestModel = obj;

            if nargin < 5
                degreeRange = 1:26;
            end
            if nargin < 6
                rmseThreshold = 0;
            end

            for d = degreeRange
                model = BasisModel(obj.mode, d);
                model.maskConvexHull = obj.maskConvexHull; % propagate flag
                model = model.fit(x, y, z);
                zhat = model.evaluate(x, y);
                rmse = sqrt(mean((z - zhat).^2, 'omitnan'));
                if rmse < bestRMSE
                    bestRMSE = rmse;
                    bestModel = model;
                end
                if bestRMSE <= rmseThreshold
                    break;
                end
            end
        end

        function [coeffVector, basisFunc, DataSet,bestModel] = fitFromTable(obj, InputTable, varName)
            if ~isvarofTable(InputTable, 'Id_Peak')
                [InputTable.Id_Peak, InputTable.Iq_Peak] = pkgamma2dq(InputTable.Is, InputTable.("Current Angle"));
            end

            [xData, yData, zData] = prepareSurfaceData(InputTable.Id_Peak, InputTable.Iq_Peak, InputTable.(varName));

            [bestModel, bestRMSE] = obj.fitBestDegree(xData, yData, zData);

            coeffVector = bestModel.coeff;
            basisFunc = @(x, y) reshape(bestModel.evaluate(x, y), size(x));

            DataSet.xData = xData;
            DataSet.yData = yData;
            DataSet.zData = zData;
            DataSet.varName = varName;
            DataSet.originDqTable = InputTable;
            DataSet.originDqTable.Properties.Description = 'Training';
            DataSet.ValidationDqTable = InputTable;
            DataSet.ValidationDqTable.Properties.Description = 'Dummy';
            DataSet.statics.rmse = bestRMSE;
        end
    end
end


function [xNorm, yNorm, mu, sigma] = normalize2d(x, y)
    mu = [mean(x), mean(y)];
    sigma = [std(x), std(y)];
    xNorm = (x - mu(1)) ./ sigma(1);
    yNorm = (y - mu(2)) ./ sigma(2);
end

function Phi = createPolyBasis(x, y, degree)
    Phi = [];
    for i = 0:degree
        for j = 0:(degree - i)
            Phi = [Phi, (x.^i).*(y.^j)];
        end
    end
end

function [Phi, centers] = createRBFBasis(x, y, numCenters, centers)
    if nargin < 4 || isempty(centers)
        theta = linspace(0, 2*pi, numCenters+1); theta(end) = [];
        cx = cos(theta);
        cy = sin(theta);
    else
        cx = centers(:, 1);
        cy = centers(:, 2);
    end
    sigma = 1.0;
    Phi = [];
    for k = 1:length(cx)
        r2 = (x - cx(k)).^2 + (y - cy(k)).^2;
        Phi = [Phi, exp(-r2 / (2 * sigma^2))];
    end
    centers = [cx(:), cy(:)];
end

function Phi = createChebyshevBasis(x, y, degree)
    Tx = chebyshevPolys(x, degree);
    Ty = chebyshevPolys(y, degree);
    Phi = kron(Ty, ones(1, size(Tx, 2))) .* kron(ones(1, size(Ty, 2)), Tx);
end

function Phi = createLegendreBasis(x, y, degree)
    Lx = legendrePolys(x, degree);
    Ly = legendrePolys(y, degree);
    Phi = kron(Ly, ones(1, size(Lx, 2))) .* kron(ones(1, size(Ly, 2)), Lx);
end

function [Phi, centers] = createThinPlateBasis(x, y, numCenters, centers)
    if nargin < 4 || isempty(centers)
        [cx, cy] = chooseThinPlateCenters(x, y, numCenters);
    else
        cx = centers(:,1); cy = centers(:,2);
    end
    N = length(x);
    M = length(cx);
    Phi = zeros(N, M);

    for k = 1:M
        r = sqrt((x - cx(k)).^2 + (y - cy(k)).^2);
        r(r == 0) = 1e-10;
        Phi(:, k) = (r.^2) .* log(r);
    end
    centers = [cx(:), cy(:)];
end

function [cx, cy] = chooseThinPlateCenters(x, y, numCenters)
    x = x(:); y = y(:);
    gridSize = ceil(sqrt(numCenters));
    xlin = linspace(min(x), max(x), gridSize);
    ylin = linspace(min(y), max(y), gridSize);
    [CX, CY] = meshgrid(xlin, ylin);
    cx = CX(:);
    cy = CY(:);
    if length(cx) > numCenters
        cx = cx(1:numCenters);
        cy = cy(1:numCenters);
    end
end

function T = chebyshevPolys(x, n)
    x = x(:);
    T = ones(length(x), n+1);
    if n >= 1, T(:,2) = x; end
    for k = 2:n
        T(:,k+1) = 2*x.*T(:,k) - T(:,k-1);
    end
end

function P = legendrePolys(x, n)
    x = x(:);
    P = zeros(length(x), n+1);
    P(:,1) = 1;
    if n >= 1, P(:,2) = x; end
    for k = 2:n
        P(:,k+1) = ((2*k - 1)*x.*P(:,k) - (k - 1)*P(:,k-1)) / k;
    end
end
