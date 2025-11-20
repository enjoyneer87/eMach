function Kv = Ke2Kv(Ke)
% Ke_to_Kv  Convert Ke [V·s/rad] -> Kv [rpm/V]
% Ke: back-EMF constant in V·s/rad (mechanical rad/s)
% Kv: speed constant in rpm/V
    Kv = (60/(2*pi)) ./ Ke;
end
