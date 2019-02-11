clc
clear
[mn, doc] = mn_open();
set(mn, 'Visible', true);
mn_d_setDefaultLengthUnit(doc, 'millimeters', false);

for i = 1:4
    
    arc(i) = compArc('name', ['arc' num2str(i)], ...
        'dim_d_a', dimMillimeter(4), ...
        'dim_r_o', dimMillimeter(80), ...
        'dim_depth', dimMillimeter(9), ...
        'dim_alpha', dimDegree(45).toRadians, ...
        'material', matGeneric('name', 'pm'), ...
        'location', clocation('anchor_xyz', dimMillimeter([0,0,0]), ...
                        'rotate_xyz', dimDegree([0,0,90*(i-1)]).toRadians));

    %mn_makeArcComponent(mn, arc(i));
    arc_segs = mn_drawArc(mn, arc(i));
    mn_dv_viewAll(mn);
end