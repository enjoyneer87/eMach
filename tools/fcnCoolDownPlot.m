function [cool_down_data legend_name_experiment]=fcnCoolDownPlot(op1_temp,xTime)
% Find Peak Value of Tem
[row col] = find(op1_temp.Variables==max(max(op1_temp.Variables)));
max_value_sensor=op1_temp.Properties.VariableNames(unique(col));
% max_instanse=op1_temp.Time(max(row));

% op1_temp=table2timetable(op1_temp,'TimeStep',seconds(0.1),"StartTime",seconds(0));
% op1_temp_timetable=table2timetable(op1_temp,'TimeStep',seconds(0.1),"StartTime",seconds(0));

% cool_down_data=op1_temp_timetable(max(row):end,:);
cool_down_data=op1_temp(max(row):end,:);
legend_name_experiment={};

for i=2:width(cool_down_data)
    if cool_down_data.(cool_down_data.Properties.VariableNames{i})>0
    legend_name_experiment=[legend_name_experiment; cool_down_data.Properties.VariableNames{i}];
    plot(cool_down_data.(cool_down_data.Properties.VariableNames{i}),'DisplayName',cool_down_data.Properties.VariableNames{i})
    hold on
    ylabel("Temperature")
    xlabel("seconds")
    legend
end

% Get Initial Data of Test data

% initial_=cool_down_data.

% % retime_endtime=op1_temp(end/10,:);
% retime_cool_down_data_retime=op1_temp(max(row):end/10,:);
% retime_cool_down_data_retime=table2timetable(retime_cool_down_data_retime,'TimeStep',seconds(0.1),"StartTime",seconds(0));
% for_end=width(op1_temp)
% %for_end=8
% for_start=1
% for i=for_start:for_end
% %     subplot(2,1,1)
%     scatter(seconds(retime_cool_down_data_retime.Time),retime_cool_down_data_retime.(retime_cool_down_data_retime.Properties.VariableNames{i}),'DisplayName',retime_cool_down_data_retime.Properties.VariableNames{i})
%     hold on
%     ylabel("Temperature")
%     xlabel("seconds")
%     legend
% end
% hold on
% 
% 
% 
% 
% initial_ambient=retime_cool_down_data_retime.("ambient temp")(1);
% initial_stator_winding=retime_cool_down_data_retime.("V")(1);
% 
% cool_down_end_time=seconds(retime_cool_down_data_retime.Time(end));
% cool_down_start_time=seconds(retime_cool_down_data_retime.Time(1));

%
% Time_range=[cool_down_start_time:seconds(0.1):cool_down_end_time]'
% reTime_range=[0:seconds(0.1):cool_down_end_time-cool_down_start_time]';
% cool_down_data_retime=retime(cool_down_data,reTime_range);
% cool_down_data_retime=lag(cool_down_data_retime,-920);
end