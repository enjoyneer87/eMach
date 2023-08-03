function time_before_spmd = dispDateTime(message_on, NumberOfPorts, NumberOfCases)
    if message_on>0
        time_before_spmd=datetime;
        disp(['The ', num2str(NumberOfPorts), ' ports ', num2str(NumberOfCases), ' cases spmd start'])
        disp(['Time at spmd start : ', char(time_before_spmd)])
    end
end