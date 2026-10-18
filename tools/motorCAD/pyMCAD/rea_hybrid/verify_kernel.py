"""Independent algebraic/manufactured checks, not native-output validation."""
import json
import math
from pathlib import Path
from .hybrid_kernel import (MU0, skin_depth_m, high_frequency_factor,
    rectangular_proximity_coefficient, line_statistic, interior_points,
    polynomial_band_weights, cuboid_side_proximity,
    rectangular_skin_coefficient, native_rectangular_skin_loss,native_last_graph_block_mean)

checks = []


def check(name, condition, detail=None):
    checks.append(dict(name=name, passed=bool(condition), detail=detail))
    assert condition, name


def near(a, b, tol=1e-12):
    return abs(a-b) <= tol*max(abs(a), abs(b), 1e-300)


rho = 2.13e-8
f = 8000*4/60
check('native numeric pi-mu0 constant', near((math.pi*MU0)**2,1.5585454565440385e-11))
check('native skin-depth constant', near(math.pi*MU0,3.947841760435743e-6))
d = skin_depth_m(f,rho)
check('diffusion skin-depth identity', near(2/(MU0*(2*math.pi*f)/rho), d*d))
errors=[]
for x in [1.00001,1.2,2,3,4,6,10,20,50]:
    direct=min(1/x,math.exp(x/8)*6/x**3*(math.sinh(x)-math.sin(x))/(math.cosh(x)+math.cos(x)))
    errors.append(abs(high_frequency_factor(x,1)-direct))
check('stable correction vs literal native expression',max(errors)<2e-15, max(errors))
check('correction threshold and legacy branch',high_frequency_factor(1,1)==1 and high_frequency_factor(4,1,0)==.25)
check('improved branch is actually active',high_frequency_factor(6,1,1)<1/6)
s=line_statistic([1,3],[True,True])
check('spatial mean-square differs from square-of-mean',s.mean_square_b_t2==5 and s.mean_b_t**2==4)
s2=line_statistic([2,999,2,999],[True,False,True,False])
check('outside-slot samples excluded',s2.valid_count==2 and s2.valid_fraction==.5 and s2.mean_square_b_t2==4)
pts=interior_points((0,0),(11,22),10)
check('ten interior samples exclude endpoints',pts[0]==(1,2) and pts[-1]==(10,20))
w=polynomial_band_weights(30,0,30)
check('polynomial band partition sums to one',near(math.fsum(w),1) and w[0]>w[-1])
K=rectangular_proximity_coefficient(.15,.003711,.00115,f,rho)
uniform=line_statistic([.8]*10,[True]*10)
one=cuboid_side_proximity(K,[1],[uniform],1,6,48)
many=cuboid_side_proximity(K,w,[uniform]*30,1,6,48)
check('uniform-field line partition invariance',near(one,many))
check('left-right factor and conductor multiplicity',near(2*one,K*6*48*.8**2))
clip=cuboid_side_proximity(1,[1,1],[s,s2],1,2,1)
check('valid-area normalization',near(clip,(5+.5*4)/1.5))
try:
    cuboid_side_proximity(1,[1],[line_statistic([0],[False])],1,2,1)
    empty_rejected=False
except ValueError:
    empty_rejected=True
check('empty geometry fails explicitly',empty_rejected)
k1=rectangular_proximity_coefficient(.15,.003711,.0002,100,rho)
k2=rectangular_proximity_coefficient(.15,.003711,.0002,200,rho)
check('low-frequency quadratic scaling',near(k2/k1,4))
native_ks=(3.711/2*.001)**4*1.5585454565440385e-11/rho/96*((3.711/1.686-1)*64/15+1.2732395447351628)/(3.711/1.686)
check('rectangular skin coefficient units and aspect ratio',near(native_ks,rectangular_skin_coefficient(.003711,.001686,rho)))
p1=native_rectangular_skin_loss(5,f,.003711,.001686,rho,.0001)
p2=native_rectangular_skin_loss(10,f,.003711,.001686,rho,.0001)
check('skin current squared scaling',near(p2/p1,4))
check('native last graph block excludes preceding boundary',
      native_last_graph_block_mean([999]+[1]*128+[3]*128,128)==3)
try:
    native_last_graph_block_mean([1]*128,128)
    incomplete_rejected=False
except ValueError:
    incomplete_rejected=True
check('incomplete graph vector rejected',incomplete_rejected)
result=dict(status='PASS',test_count=len(checks),checks=checks,
            validation_scope='Algebra and constructed fields only; zero native-output parity measurements',
            native_end_to_end_validated=False)

print(json.dumps(dict(status=result['status'],test_count=len(checks),native_end_to_end_validated=False)))
