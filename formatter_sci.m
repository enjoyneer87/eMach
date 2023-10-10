set(gca,'FontName','Times New Roman','FontSize',20);

% set(gca,'FontSize',14)
grid on
% legend
ax = gca;
ax.XLabel.FontName = 'Times New Roman';
ax.YLabel.FontName = 'Times New Roman';
box on
% ax.XLabel.String=HDEV_measured.I1(1).time.Properties.VariableNames
% ax.YLabel.String=convertCharsToStrings(HDEV_measured.I1(1).value.Properties.Description)
% 
% ax.Legend.String={'a','b','c','mean d','mean q','d','q'}