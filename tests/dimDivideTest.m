% Test the DimLinear / operator

oneInch   = DimInch(1);
twoInches = DimInch(2);

oneMillimeter  = DimMillimeter(1);
twoMillimeters = DimMillimeter(2);

tol = 1e-5;

%% Test 1: mrdivide of scalar

val = oneInch / 2;
expected = DimInch(0.5);
assert(strcmp(class(val), class(expected)));
assert(abs(val - expected) < tol);


val = oneMillimeter / 2;
expected = DimMillimeter(0.5);
assert(strcmp(class(val), class(expected)));
assert(abs(val - expected) < tol);


val = oneMillimeter / -5;
expected = DimMillimeter(-0.2);
assert(strcmp(class(val), class(expected)));
assert(abs(val - expected) < tol);


val = twoInches / 8;
expected = DimInch(0.25);
assert(strcmp(class(val), class(expected)));
assert(abs(val - expected) < tol);
