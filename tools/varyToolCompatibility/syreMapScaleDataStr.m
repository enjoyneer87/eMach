function data=syreMapScaleDataStr()

% Save data in the output structure
mapScale.l          = l;
mapScale.Ns         = Ns;
mapScale.kL         = kL;
mapScale.kN         = kN;
mapScale.Rs         = Rs;
mapScale.T          = T;
mapScale.n          = n;
mapScale.id         = id;
mapScale.iq         = iq;
mapScale.fd         = fd;
mapScale.fq         = fq;
mapScale.loss       = loss;
mapScale.kj         = kj;
mapScale.PF         = sin(atan2(mapScale.iq,mapScale.id)-atan2(mapScale.fq,mapScale.fd));

if isfield(motorModel,'geo')
    mapScale.J = abs(mapScale.id+j*mapScale.iq)/sqrt(2)/(motorModel.geo.Aslot*motorModel.geo.win.kcu).*(Ns/(motorModel.data.p*motorModel.geo.q));
else
    mapScale.J = NaN;
end
mapScale.motorModel = motorModel;


end






