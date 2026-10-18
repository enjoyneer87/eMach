"""Local, independent mathematical reconstruction of the inspected v261 path.

Evidence: MotorCAD.exe SHA256 488be07c3ac4a82fd1f737aad76ff6b6df415ba82f5f05adf85c7f7f7f5ca323.
This is NOT an end-to-end Motor-CAD clone. It consumes already resolved native
bundle dimensions, segment geometry, valid-slot masks and scalar B samples.
It does not implement the proprietary FEA interpolator, geometry engine,
temperature network, slice scheduling or selection of actual saved graph data.
All quantities are SI unless an argument explicitly says otherwise.
"""
import math
from dataclasses import dataclass
from typing import Sequence

MU0 = 4e-7 * math.pi


def _positive(**values):
    for name, value in values.items():
        if not math.isfinite(value) or value <= 0:
            raise ValueError('%s must be finite and positive' % name)


def skin_depth_m(frequency_hz, resistivity_ohm_m):
    """0xa56ed0; its native return value is mm (converted here to SI)."""
    _positive(resistivity_ohm_m=resistivity_ohm_m)
    if frequency_hz < 0 or not math.isfinite(frequency_hz):
        raise ValueError('frequency must be finite and nonnegative')
    if frequency_hz == 0:
        return math.inf
    return math.sqrt(resistivity_ohm_m / (math.pi * MU0 * frequency_hz))


def high_frequency_factor(bundle_height_m, delta_m, method=1):
    """0xa576e0: correction is active ONLY when h/delta > 1.

    Native method 1 takes min(improved expression, delta/h); other observed
    integer values take delta/h. Require explicit 0 or 1 here to catch typos.
    The numerically stable equivalent below avoids sinh/cosh overflow; extreme
    floating-point behavior is therefore intentionally not a binary emulator.
    """
    _positive(bundle_height_m=bundle_height_m)
    if delta_m <= 0 or math.isnan(delta_m):
        raise ValueError('invalid skin depth')
    if method not in (0, 1):
        raise ValueError('supported recorded methods: 0 or 1')
    x = bundle_height_m / delta_m
    if x <= 1:
        return 1.0
    cap = 1.0 / x
    if method == 0:
        return cap
    em = math.exp(-x)
    ratio = (1-em*em-2*em*math.sin(x))/(1+em*em+2*em*math.cos(x))
    log_improved = x/8 + math.log(6) - 3*math.log(x) + math.log(ratio)
    return cap if log_improved >= math.log(cap) else math.exp(log_improved)


def rectangular_proximity_coefficient(length_m, bundle_width_m, bundle_height_m,
                                      frequency_hz, resistivity_ohm_m,
                                      high_frequency_method=1):
    """0xa576e0; coefficient multiplying scalar spatial mean(B**2).

    Width and height are ACLosses_BundleWidth/Height, NOT interchangeable
    historical Python DIMS names. Native code explicitly multiplies f by 2*pi.
    Pass the resolved current ArmatureConductor_Resistivity. Do not apply a
    second temperature correction to this coefficient.
    Native length is coil-stack + front/rear clamp plates, times slice factor.
    """
    _positive(length_m=length_m, bundle_width_m=bundle_width_m,
              bundle_height_m=bundle_height_m, resistivity_ohm_m=resistivity_ohm_m)
    delta = skin_depth_m(frequency_hz, resistivity_ohm_m)
    return (length_m*bundle_width_m*bundle_height_m**3/resistivity_ohm_m
            * (2*math.pi*frequency_hz)**2/12
            * high_frequency_factor(bundle_height_m, delta, high_frequency_method))


@dataclass(frozen=True)
class LineStatistic:
    requested_count: int
    valid_count: int
    valid_fraction: float
    mean_b_t: float
    mean_square_b_t2: float
    rms_b_t: float


def line_statistic(b_samples_t: Sequence[float], valid: Sequence[bool]):
    """0xa59ef0: spatial statistics, NOT temporal/harmonic RMS.

    Sample locations are j/(m+1), j=1..m; endpoints are excluded. Invalid-slot
    samples contribute neither to the numerator nor valid count.
    """
    if not b_samples_t or len(b_samples_t) != len(valid):
        raise ValueError('nonempty matching samples and validity mask required')
    values = [float(b) for b, ok in zip(b_samples_t, valid) if ok]
    if any(not math.isfinite(b) for b in values):
        raise ValueError('nonfinite valid B sample')
    m, n = len(b_samples_t), len(values)
    mean = math.fsum(values)/n if n else 0.0
    ms = math.fsum(b*b for b in values)/n if n else 0.0
    return LineStatistic(m, n, n/m, mean, ms, math.sqrt(ms))


def interior_points(start_xy, end_xy, count=10):
    if count < 1 or len(start_xy) != 2 or len(end_xy) != 2:
        raise ValueError('two endpoints and positive count required')
    return [tuple(a+(j/(count+1))*(b-a) for a,b in zip(start_xy,end_xy))
            for j in range(1,count+1)]


def polynomial_band_weights(total_lines, lines_used, lines_in_cuboid,
                            power=2.5, offset=1.1, reciprocal_power=False):
    """0xa57ee0/0xa58fc0 band thicknesses within one resolved cuboid.

    Geometry coordinates and allocation of lines to cuboids are inputs, not
    inferred from a generic rectangle. Special axial/outer-rotor branch may
    invert power; callers must resolve that branch explicitly.
    """
    _positive(power=power, offset=offset)
    a = math.ceil(total_lines*offset)-lines_used
    n = lines_in_cuboid
    if n < 1 or a < n:
        raise ValueError('invalid native line allocation')
    p = 1/power if reciprocal_power else power
    d = abs(a**p-(a-n)**p)
    return [abs((a-j)**p-(a-j-1)**p)/d for j in range(n)]


def cuboid_side_proximity(coefficient_w_per_t2, line_areas,
                         stats: Sequence[LineStatistic],
                         conductor_fraction, conductors_per_slot_total,
                         slot_number, total_strands=1, adjustment_factor=1.0):
    """0xa5bb30 algebra; ONE cuboid and ONE left/right side.

    P = K * AF * Q * (g*N/(2*S)) * sum(a*s*meanB2)/sum(a*s).
    Native a is area/sum(area), s is valid-sample fraction. The two native
    normalizations cancel as written here. The factor 1/2 is the side count
    allocation in this routine; it is NOT a peak-to-RMS conversion.
    """
    if len(line_areas) != len(stats) or not stats:
        raise ValueError('matching lines and statistics required')
    if any(not math.isfinite(a) or a < 0 for a in line_areas):
        raise ValueError('invalid segment area')
    _positive(total_strands=total_strands, slot_number=slot_number,
              conductors_per_slot_total=conductors_per_slot_total,
              conductor_fraction=conductor_fraction)
    weights = [a*s.valid_fraction for a,s in zip(line_areas,stats)]
    denominator = math.fsum(weights)
    if denominator <= 0:
        # Native all-empty cuboid can divide by zero; reject instead of claiming
        # it is a physical zero-loss result.
        raise ValueError('no sampled slot area; geometry/interpolation unresolved')
    field = math.fsum(w*s.mean_square_b_t2 for w,s in zip(weights,stats))/denominator
    return (coefficient_w_per_t2*adjustment_factor*slot_number
            * conductor_fraction*conductors_per_slot_total/(2*total_strands)*field)


def rectangular_skin_coefficient(copper_width_m, copper_height_m, resistivity_ohm_m):
    """0xa5d5e0, native Copper_Width/Copper_Height order is deliberate."""
    _positive(copper_width_m=copper_width_m, copper_height_m=copper_height_m,
              resistivity_ohm_m=resistivity_ohm_m)
    ratio = copper_width_m/copper_height_m
    return ((copper_width_m/2)**4*(math.pi*MU0)**2/resistivity_ohm_m/96
            * (4/math.pi+64*(ratio-1)/15)/ratio)


def native_rectangular_skin_loss(current_density_arms_per_mm2, frequency_hz,
                                copper_width_m, copper_height_m,
                                resistivity_ohm_m, native_copper_volume_m3):
    """0xa5d760; native volume is total armature Cu mass / active Cu density.

    This getter path is not proven to be active-length-only. Match the exact
    native mass scope before comparing with an active-only Full-FEA label.
    """
    _positive(native_copper_volume_m3=native_copper_volume_m3)
    ks = rectangular_skin_coefficient(copper_width_m,copper_height_m,resistivity_ohm_m)
    return 2*ks*(current_density_arms_per_mm2*1e6*frequency_hz)**2*native_copper_volume_m3


def native_last_graph_block_mean(values, requested_count):
    """0x1a6b950 -> 0x1a6bf30 -> 0x1a6c270, selected block index -1.

    Caller must supply the SAME native graph vector/count semantics. For the
    usual initial sample + complete blocks, the initial boundary is excluded.
    Invalid/incomplete ranges are rejected instead of reproducing native silent
    zero. This does not identify the graph vector for a particular saved case.
    """
    count=len(values)
    n=requested_count
    if n < 1 or count == 0 or any(not math.isfinite(v) for v in values):
        raise ValueError('invalid graph input')
    if count == 1 and n == 1:
        return float(values[0])
    if count < n+1:
        raise ValueError('native graph range is incomplete')
    block=count//n-1
    start=block if n==1 else block*n+1
    end=start if n==1 else (block+1)*n
    if start<0 or end>=count:
        raise ValueError('native endpoint convention is not satisfied')
    return math.fsum(values[start:end+1])/n
