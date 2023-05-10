
% scatter_plot_handles(1) = subplot(3, 1, 1);
% figure1 = figure;
line(ToyotaPriusspeedIdIq7507500.VarName1,ToyotaPriusspeedIdIq7507500.VarName3,displayname='iq',color='red')
% axes 생성
ax=gca;
ax.XLim1=[750 7500]

hold on
line(ToyotaPriusspeedIdIq7507500.VarName1,ToyotaPriusspeedIdIq7507500.VarName2,displayname='id')
legend

  