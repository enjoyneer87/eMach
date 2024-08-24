function portNumber=getPCRDPPortNumber()
    [status, cmdout] = system('reg query "HKEY_LOCAL_MACHINE\System\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp" /v PortNumber');
    if status == 0
        % Extract the port number from the output
        portNumberStr = regexp(cmdout, 'PortNumber\s+REG_DWORD\s+(\w+)', 'tokens', 'once');
        portNumber = hex2dec(portNumberStr{1});
        fprintf('RDP Port Number: %d\n', portNumber);
    else
        fprintf('Failed to query the registry.\n');
    end
end