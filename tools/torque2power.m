function PowerInW=torque2power(Nm,rpm)
    radsec = rpm2radsec(rpm);
    PowerInW  =Nm .*(radsec);
end