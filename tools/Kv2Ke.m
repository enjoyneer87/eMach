function Ke = Kv2Ke(Kv)
% Kv_to_Ke  Convert Kv [rpm/V] -> Ke [V·s/rad]
% Kv: speed constant in rpm/V
% Ke: back-EMF constant in V·s/rad (mechanical rad/s)
    Ke = (60/(2*pi)) ./ Kv;
end
