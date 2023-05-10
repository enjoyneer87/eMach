function fun_idiq_map_plot(x1,y1,name1,x2,y2,name2)
scatter(x1,y1,Marker='x',DisplayName=name1);
xlabel('Torque[Nm]');
ylabel('Force Density[N/m^2]');
legend
hold on
scatter(x2,y2,Marker='x',DisplayName=name2);

grid on

end