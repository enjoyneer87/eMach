function af = jeetPredictAF(scale, speedRpm, irmsA, phaseDeg)
%JEETPREDICTAF  Evaluate the calibrated amplification factor AF.
%
%   af = jeetPredictAF('SC', 16000, 690, 36)          scalar
%   af = jeetPredictAF('SC', speedVec, irmsVec, betaVec)  element-wise
%
%   Inputs are broadcast like numpy: pass equal-size arrays, or scalars
%   mixed with one array.
%
%   Example (AF vs. beta sweep at rated current):
%       beta = 0:2:90;
%       af = jeetPredictAF('SC', 16000, 920, beta);
%       plot(beta, af)

pl = jeetGetPipeline();

toNp = @(v) py.numpy.array(v(:).');
out = pl.predict_af(scale, toNp(double(speedRpm)), ...
    toNp(double(irmsA)), toNp(double(phaseDeg)));

if isa(out, 'py.numpy.ndarray')
    af = np2mat(out);
else
    af = double(out);
end
end
