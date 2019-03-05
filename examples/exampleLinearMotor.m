clc
clear

DRAW_MAGNET = 1;
DRAW_TIKZ   = 0;

% stator iron parameters
w_s = 65.7;
w_st = 14.8;
w_so = 3.66;
r_so = 71.8;
r_si = 35.9;
d_so = 3.98;
d_sp = 7.46;
d_sy = 9.53;
r_st = 3; r_sf = 3; r_sb = 3;

% mover iron parameters
g = 1.35; d_rm = 9.82; r_ri = 17.6;
w_ra = 8.24; w_rr = 12.9;
w = 65.7;
w_n = (w - w_ra - 2*w_rr)/2;
d = r_si - g - d_rm - r_ri;
d_n = 3;

r_ri = r_si - g - d - d_n;

%% Define cross sections

statorIron = CrossSectLinearMotorStator( ...
        'name', 'stator_iron', ...
        'dim_w_s', DimMillimeter(w_s), ...
        'dim_w_st', DimMillimeter(w_st), ...
        'dim_w_so', DimMillimeter(w_so), ...
        'dim_r_so', DimMillimeter(r_so), ...
        'dim_r_si', DimMillimeter(r_si), ...
        'dim_d_so', DimMillimeter(d_so), ...
        'dim_d_sp', DimMillimeter(d_sp), ...
        'dim_d_sy', DimMillimeter(d_sy), ...
        'dim_r_st', DimMillimeter(r_st), ...
        'dim_r_sf', DimMillimeter(r_sf), ...
        'dim_r_sb', DimMillimeter(r_sb), ...
        'location', Location2D( ...
            'anchor_xy', DimMillimeter([0,0]), ...
            'theta', DimDegree([0]).toRadians() ...
        ) ...
        );
 
moverIron = CrossSectNotchedRectangle( ...
        'name', 'mover_iron', ...
        'dim_w', DimMillimeter(w), ...
        'dim_w_n', DimMillimeter(w_n), ...   
        'dim_d', DimMillimeter(d), ...
        'dim_d_n', DimMillimeter(d_n), ...         
        'location', Location2D( ...
            'anchor_xy', DimMillimeter([-w, r_ri]), ...
            'theta', DimDegree([-90]).toRadians() ...
        ) ...
        );    

magnet1 = CrossSectHollowRect( ...
        'name', 'magnet1', ...
        'dim_t1', DimMillimeter(d_rm/2), ...
        'dim_t2', DimMillimeter(w_rr/2), ...
        'dim_t3', DimMillimeter(d_rm/2),...
        'dim_t4', DimMillimeter(w_rr/2),...
        'dim_w',DimMillimeter(d_rm),...
        'dim_h',DimMillimeter(w_rr),...
        'location', Location2D( ...
            'anchor_xy', DimMillimeter([d,w - w_n - w_rr]), ...
            'theta', DimDegree([0]).toRadians() ...
        ) ...
        );    

magnet2 = CrossSectHollowRect( ...
        'name', 'magnet2', ...
        'dim_t1', DimMillimeter(d_rm/2), ...
        'dim_t2', DimMillimeter(w_ra/2), ...
        'dim_t3', DimMillimeter(d_rm/2),...
        'dim_t4', DimMillimeter(w_ra/2),...
        'dim_w',DimMillimeter(d_rm),...
        'dim_h',DimMillimeter(w_ra),...
        'location', Location2D( ...
            'anchor_xy', DimMillimeter([d,w_n + w_rr]), ...
            'theta', DimDegree([0]).toRadians() ...
        ) ...
        ); 

magnet3 = CrossSectHollowRect( ...
        'name', 'magnet1', ...
        'dim_t1', DimMillimeter(d_rm/2), ...
        'dim_t2', DimMillimeter(w_rr/2), ...
        'dim_t3', DimMillimeter(d_rm/2),...
        'dim_t4', DimMillimeter(w_rr/2),...
        'dim_w',DimMillimeter(d_rm),...
        'dim_h',DimMillimeter(w_rr),...
        'location', Location2D( ...
            'anchor_xy', DimMillimeter([d,w_n]), ...
            'theta', DimDegree([0]).toRadians() ...
        ) ...
        ); 

%% Define components

statorIronComp = Component( ...
        'name', 'comp1', ...
        'crossSections', statorIron, ...
        'material', MaterialGeneric('name', 'iron'), ...
        'makeSolid', MakeSimpleExtrude( ...
            'location', Location3D( ...
                'anchor_xyz', DimMillimeter([0,0,0]), ...
                'rotate_xyz', DimDegree([0,0,0]).toRadians() ...
                ), ...
            'dim_depth', DimMillimeter(40)) ...
        );

moverIronComp = Component( ...
        'name', 'comp1', ...
        'crossSections', moverIron, ...
        'material', MaterialGeneric('name', 'iron'), ...
        'makeSolid', MakeSimpleExtrude( ...
            'location', Location3D( ...
                'anchor_xyz', DimMillimeter([0,0,0]), ...
                'rotate_xyz', DimDegree([0,0,0]).toRadians() ...
                ), ...
            'dim_depth', DimMillimeter(40)) ...
        );    

magnet1Comp = Component( ...
        'name', 'comp1', ...
        'crossSections', magnet1, ...
        'material', MaterialGeneric('name', 'pm'), ...
        'makeSolid', MakeSimpleExtrude( ...
            'location', Location3D( ...
                'anchor_xyz', DimMillimeter([0,0,0]), ...
                'rotate_xyz', DimDegree([0,0,0]).toRadians() ...
                ), ...
            'dim_depth', DimMillimeter(40)) ...
        );    
    
magnet2Comp = Component( ...
        'name', 'comp1', ...
        'crossSections', magnet2, ...
        'material', MaterialGeneric('name', 'pm'), ...
        'makeSolid', MakeSimpleExtrude( ...
            'location', Location3D( ...
                'anchor_xyz', DimMillimeter([0,0,0]), ...
                'rotate_xyz', DimDegree([0,0,0]).toRadians() ...
                ), ...
            'dim_depth', DimMillimeter(40)) ...
        );    

magnet3Comp = Component( ...
        'name', 'comp1', ...
        'crossSections', magnet3, ...
        'material', MaterialGeneric('name', 'pm'), ...
        'makeSolid', MakeSimpleExtrude( ...
            'location', Location3D( ...
                'anchor_xyz', DimMillimeter([0,0,0]), ...
                'rotate_xyz', DimDegree([0,0,0]).toRadians() ...
                ), ...
            'dim_depth', DimMillimeter(40)) ...
        );  
    
%% Draw via MagNet

if (DRAW_MAGNET)
    toolMn = MagNet();
    toolMn.open(0,0,true);
    toolMn.setDefaultLengthUnit('millimeters', false);

    statorIronComp.make(toolMn, toolMn);
    moverIronComp.make(toolMn, toolMn);
    magnet1Comp.make(toolMn, toolMn);
    magnet2Comp.make(toolMn, toolMn);
    magnet3Comp.make(toolMn, toolMn);

    toolMn.viewAll();
end

%% Draw via TikZ

if (DRAW_TIKZ)
    toolTikz = TikZ();
    toolTikz.open('output.txt');

    comp1.make(toolTikz);
    statorIronComp.make(toolTikz);
    moverIronComp.make(toolTikz);
    magnet1Comp.make(toolTikz);
    magnet2Comp.make(toolTikz);
    magnet3Comp.make(toolTikz);
    toolTikz.close();
end
