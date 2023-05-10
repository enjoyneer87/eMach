for i=1:1:39
    scatter3(idse_map(:,i),iqse_map(:,i),torque_idiq_map(:,i));
    hold on
end

for i=1:1:39

    scatter3(Id_Peak(1+60*(i-1):60*i),Iq_Peak(1+60*(i-1):60*i),Shaft_Torque(1+60*(i-1):60*i),'filled');
    hold on
end

scatter(Effi1st.pk(1:16),Effi1st.VarName4(1:16))
I_pk - beta -torque 
hold on
for i=1:1:Speed(length(Speed))/250
speed_list=find(Speed==250*i)
name=string(250*i)
name=strcat('rpm=',name)
a=length(speed_list)

scatter3(Stator_Current_Phase_Peak((i-1)*a+1:i*a,:) ,Phase_Advance((i-1)*a+1:i*a,:),Shaft_Torque((i-1)*a+1:i*a,:),'DisplayName',name)

hold on
end

% Ipk - beta -Vabs motorcad
hold on
for i=4
speed_list=find(Speed==1300);
name=string(1300)
name=strcat('rpm=',name);
a=length(speed_list);
Speed(speed_list)
Vabs
scatter3(Stator_Current_Phase_Peak((i-1)*a+1:i*a,:) ,Phase_Advance((i-1)*a+1:i*a,:),Voltage_Line_RMS((i-1)*a+1:i*a,:),'DisplayName',name)
scatter3(Phase_Advance(481:speed_list(a)),Voltage_Phase_Peak(481:speed_list(a)))
hold on
Vd
scatter3(Stator_Current_Phase_Peak((i-1)*a+1:i*a,:) ,Phase_Advance((i-1)*a+1:i*a,:),Vd_RMS((i-1)*a+1:i*a,:),'DisplayName',name)
hold on
Vq
scatter3(Phase_Advance((i-1)*a+1:i*a,:),Vd_RMS((i-1)*a+1:i*a,:),Stator_Current_Phase_Peak((i-1)*a+1:i*a,:), 'DisplayName',name)

hold on
end



hold on
for i=8
find(Effi1st.VarName1==500*i)
name=string(500*i)
name=strcat('rpm=',name)
a=72*ones(length(ans),1);

plot3(Effi1st.pk(ans),a,Effi1st.VarName4(ans),'DisplayName',name)

hold on
end