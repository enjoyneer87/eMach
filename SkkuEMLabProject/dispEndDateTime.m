function dispEndDateTime(message_on, NumberOfPorts, NumberOfCases, time_before_spmd)
if message_on>0
    time_after_spmd=datetime;
    disp(['The ', num2str(NumberOfPorts), ' ports', num2str(NumberOfCases), 'cases spmd end'])
    disp(['Time at spmd end : ', char(time_after_spmd)])
    disp(['Time cost of spmd : ', char(time_before_spmd-time_after_spmd)])
end
end