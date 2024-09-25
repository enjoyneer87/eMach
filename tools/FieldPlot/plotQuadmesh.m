% QUADMESH 함수
function hh = plotQuadmesh(quad, x, y, z, varargin)

% quad=pdeQuadElements;

%QUADMESH Quadrilateral mesh plot.
% QUADMESH(QUAD,X,Y,Z,C)는 M-by-4
% 면 행렬 QUAD에 정의된 사변형을 메쉬로 표시합니다.  QUAD의 행에는
% 단일 사변형을 정의하는 X, Y, Z 정점 벡터에 대한 인덱스를 포함합니다.
% 가장자리 색은 벡터 C로 정의됩니다.
%
%   QUADMESH(QUAD,X,Y,Z) uses C = Z, so color is proportional to surface
%   height.
%
%   QUADMESH(TRI,X,Y) displays the quadrilaterals in a 2-d plot.
%
%   H = QUADMESH(...) returns a handle to the displayed quadrilaterals.
%
%   QUADMESH(...,'param','value','param','value'...) allows additional
%   patch param/value pairs to be used when creating the patch object.
%
%   See also PATCH.
%
% Script code based on copyrighted code from mathworks for TRIMESH.
% Allan P. Engsig-Karup, apek@mek.dtu.dk.
% Modified Dohyun Kang dhkang87@g.skku.edu
ax = axescheck(varargin{:});
ax = newplot(ax);


% Reshape the quad data to form the element connections


% Now plot the combined data
% Now plot the combined data

if nargin == 3 || (nargin > 4 && ischar(z))
    % d = quad([1 2 3 4 1], :);
    d = quad([1 2 3 4 1], :);  % Add the first node again to close the quad

    if nargin == 3
        % Use the d array to gather the X and Y data
        combinedXData = reshape([x(d); NaN(1, size(d, 2))], 1, []);  % Add NaN to separate the elements
        combinedYData = reshape([y(d); NaN(1, size(d, 2))], 1, []);  % Add NaN to separate the elements
        % h = plot(ax,x(d) , y(d),'Color',[0.8,0.8,0.8]);
        h = plot(ax,combinedXData, combinedYData,'Color', [0.8, 0.8, 0.8]);
        % h = plot(ax, combinedXData, combinedYData, 'Color', [0.8, 0.8, 0.8]);
    else
        h = plot(ax, x(d), y(d), z, varargin{1}, varargin{2:end});
    end
    if nargout == 1, hh = h; end
    return;
end

start = 1;
if nargin > 4 && rem(nargin - 4, 2) == 1
    c = varargin{1};
    start = 2;
else
    c = z;
end

if ischar(get(ax, 'color'))
    fc = get(gcf, 'Color');
else
    fc = get(ax, 'color');
end



% % Combine handles of lines with the same color
% if isequal(get(h1, 'Color'), get(h2, 'Color')) && isequal(get(h2, 'Color'), get(h3, 'Color'))
%     combinedHandle = [h1, h2, h3];  % Combine the lines
%     legend(combinedHandle(1), 'Combined Legend');  % Create a single legend entry
% end
% h = patch('faces', quad, 'vertices', [x(:) y(:) z(:)], 'facevertexcdata', c(:), ...
%     'facecolor', fc, 'edgecolor', get(ax, 'defaultsurfacefacecolor'), ...
%     'facelighting', 'none', 'edgelighting', 'flat', ...
%     'parent', ax, ...
%     varargin{start:end});
% 
% h = patch('faces', quad, 'vertices', [x(:) y(:) z(:)], ...
%     'facecolor', [0.8 0.8 0.8], ...  % 옅은 회색
%     'edgecolor', [0.8 0.8 0.8], ...  % 옅은 회색
%     'facelighting', 'none', 'edgelighting', 'flat', ...
%     'DisplayName', 'Mesh', ... 
%     'parent', ax, ...
%     varargin{start:end});

if ~ishold(ax)
    view(ax, 3);
    grid(ax, 'on');
end

if nargout == 1
    hh = h;
end

end
