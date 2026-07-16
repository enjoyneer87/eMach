function m = np2mat(x)
%NP2MAT  Convert a numpy ndarray (or py scalar/list) to a MATLAB double.
%
%   Handles 0-D/1-D/2-D arrays. C-order flattening is undone on the
%   MATLAB side, so 2-D arrays keep their (row, col) layout.

if isa(x, 'double')
    m = x;
    return
end
if isa(x, 'py.int') || isa(x, 'py.float')
    m = double(x);
    return
end
if isa(x, 'py.list') || isa(x, 'py.tuple')
    m = cellfun(@double, cell(x));
    return
end

% numpy ndarray
sz = cellfun(@double, cell(x.shape));
flat = cellfun(@double, cell(x.flatten('C').tolist()));
if isempty(sz)
    m = double(x.item());
elseif isscalar(sz)
    m = flat(:);
else
    m = permute(reshape(flat, fliplr(sz)), numel(sz):-1:1);
end
end
