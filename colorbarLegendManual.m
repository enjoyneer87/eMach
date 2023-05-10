% f = figure;
% surf(peaks);
% % cmap=hsv(256);
% hsvmap = hsv(64);
% 
% cmap = flipud(hsvmap);
% % indices = 10:50;
% idx = 20:64;
% 
% newmap = cmap(idx,:);
% colormap(newmap);
% 



%% data
Apotential='$[Wb/m]$'       %Apotential
rangeA=[0:0.02/10:0.02]     %rangeA
Aname='MagneticVectorA'     %Aname

B='$[T]$'                   %B
rangeB=[0.00:0.05/10:0.05]  %rangeB
Bname='FluxDensityB'        %Bname


Jeddy='$[A/mm^2]$'          %Jeddy
rangeJe=[-95:13.9:44]       %rangeJe
Jname='EddyCurrentDensity'  %Jname

%%  Set Value

textUnit    =Apotential
Ticklabel   =rangeA
figName     =Aname
%%

figure1 = figure('InvertHardcopy','off',...
    'Colormap',[0.125 0 1;0.03125 0 1;0 0.0625 1;0 0.15625 1;0 0.25 1;0 0.34375 1;0 0.4375 1;0 0.53125 1;0 0.625 1;0 0.71875 1;0 0.8125 1;0 0.90625 1;0 1 1;0 1 0.90625;0 1 0.8125;0 1 0.71875;0 1 0.625;0 1 0.53125;0 1 0.4375;0 1 0.34375;0 1 0.25;0 1 0.15625;0 1 0.0625;0.03125 1 0;0.125 1 0;0.21875 1 0;0.3125 1 0;0.40625 1 0;0.5 1 0;0.59375 1 0;0.6875 1 0;0.78125 1 0;0.875 1 0;0.96875 1 0;1 0.9375 0;1 0.84375 0;1 0.75 0;1 0.65625 0;1 0.5625 0;1 0.46875 0;1 0.375 0;1 0.28125 0;1 0.1875 0;1 0.09375 0;1 0 0],...
    'Color',[1 1 1]);

% axes 생성
axes1 = axes('Parent',figure1,...
    'Position',[0.110190476190476 0.11 0.159285650707425 0.326904943557015]);
hold(axes1,'on');

% surf 생성
surf(peaks,'Parent',axes1);

% text 생성
text('Parent',axes1,'HorizontalAlignment','center','FontWeight','bold',...
    'FontSize',14,...
    'FontName','Times New Roman',...
    'Interpreter','latex',...
    'String',[textUnit],...
    'Position',[178.463193485455 -6.22489156040115 58.5487615723203]);

view(axes1,[-37.5 30]);
grid(axes1,'on');
hold(axes1,'off');
% 나머지 axes 속성 설정
set(axes1,'FontSize',8);
% colorbar 생성
colorbar(axes1,'Position',...
    [0.45995238095238 0.0766666666666667 0.0380952380952382 0.815000000000001],...
    'Ticks',[-6 -4.6 -3.2 -1.8 -0.4 1 2.4 3.8 5.2 6.6 8],...
    'TickLabels',Ticklabel,...
    'FontSize',20,...
    'FontName','Times New Roman');

figHandles = findobj('Type', 'figure');

for i = 1:length(figHandles)
    figHandle = figHandles(i);
    figChildren = get(figHandle, 'Children');
    formatterSCI_IpkBeta
%     folderPath = 'Z:\01_Codes_Projects\Thesis_skku\Thesis_SKKU\figure'; % 저장할 폴더 경로
    folderPath='Z:\01_Codes_Projects\git_fork_emach'
%     figName=figHandle.Name
    figAxis=figHandle.Children;
    figName = strrep(figName, ' ', '_'); % 공백을 언더바로 변경
    figName = strrep(figName, '.', ''); % '.'을 제거
    filename = fullfile(folderPath, [figName '.png']); % 저장할 파일명과 경로를 합칩니다.
    exportgraphics(figHandle, filename, 'Resolution', 600,'BackgroundColor', 'none');

end

% close;


