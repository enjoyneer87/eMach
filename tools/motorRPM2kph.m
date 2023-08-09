function kph=motorRPM2kph(motorRPM,tr,gr)
    dri_shaft_rpm=motorRPM/gr;
    kph=dri_shaft_rpm/1000*(2*pi*60*tr);
end