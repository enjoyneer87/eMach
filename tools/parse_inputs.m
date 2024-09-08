function [f,ndim,loc,rowflag] = parse_inputs(f,h)

loc = {}; % spacing along the x,y,z,... directions
ndimsf = ndims(f);
ndim = ndimsf;
rowflag = false;
if isvector(f)
    ndim = 1;
    if isrow(f) % Treat row vector as a column vector
        rowflag = true;
        f = f.';
    end
end

% Default step sizes: hx = hy = hz = 1
indx = size(f);
if isempty(h)
    % gradient(f)
    loc = cell(1,ndimsf);
    for k = 1:ndimsf
        loc(k) = {1:indx(k)};
    end
elseif isscalar(h) % gradient(f,h)
    if isscalar(h{1})
        % Expand scalar step size
        loc = cell(1,ndimsf);
        for k = 1:ndimsf
            loc(k) = {h{1}*(1:indx(k))};
        end
    elseif ndim == 1
        % Check for vector case
        if numel(h{1}) ~= numel(f)
            error(message('MATLAB:gradient:InvalidGridSpacing'));
        end
        loc(1) = h(1);
    else
        error(message('MATLAB:gradient:InvalidInputs'));
    end
elseif ndimsf == numel(h)  % gradient(f,hx,hy,hz,...)
    % Swap 1 and 2 since x is the second dimension and y is the first.
    loc = h;
    if ndim > 1
        loc([2 1]) = loc([1 2]);
    end
    % replace any scalar step-size with corresponding position vector, and
    % check that the values specified in each position vector is the right
    % shape and size
    for k = 1:ndimsf
        if isscalar(loc{k})
            loc{k} = loc{k}*(1:indx(k));
        elseif ~isvector(squeeze(loc{k})) || numel(loc{k}) ~= size(f, k)
            error(message('MATLAB:gradient:InvalidGridSpacing'));
        end
    end 
else
    error(message('MATLAB:gradient:InvalidInputs'));
end
end