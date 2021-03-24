clc
clear

DRAW_MAGNET = 0;
DRAW_TIKZ   = 0;
DRAW_JMAG = 1;

%% Define cross sections

stator1 = CrossSectOuterRotorStator( ...
        'name', 'stator1', ...
        'dim_alpha_st', DimDegree(30), ...
        'dim_alpha_so', DimDegree((30 / 2) * 0.25), ...
        'dim_r_si', DimMillimeter(15), ...
        'dim_d_sy', DimMillimeter(7.5), ...
        'dim_d_st', DimMillimeter(7.5), ...
        'dim_d_sp', DimMillimeter(5), ...
        'dim_d_so', DimMillimeter(3), ...
        'dim_w_st', DimMillimeter(7.5), ...
        'dim_r_st', DimMillimeter(0), ...
        'dim_r_sf', DimMillimeter(0), ...
        'dim_r_sb', DimMillimeter(0), ...
        'dim_Q', 8, ...
        'location', Location2D( ...
            'anchor_xy', DimMillimeter([0,0]), ...
            'theta', DimDegree(0).toRadians() ...
        ) ...
);

stator2 = CrossSectOuterRotorStator( ...
        'name', 'stator2', ...
        'dim_alpha_st', DimDegree(30), ...
        'dim_alpha_so', DimDegree((30 / 2) * 0.25), ...
        'dim_r_si', DimMillimeter(15), ...
        'dim_d_sy', DimMillimeter(7.5), ...
        'dim_d_st', DimMillimeter(7.5), ...
        'dim_d_sp', DimMillimeter(5), ...
        'dim_d_so', DimMillimeter(3), ...
        'dim_w_st', DimMillimeter(7.5), ...
        'dim_r_st', DimMillimeter(0), ...
        'dim_r_sf', DimMillimeter(0), ...
        'dim_r_sb', DimMillimeter(0), ...
        'dim_Q', 8, ...
        'location', Location2D( ...
            'anchor_xy', DimMillimeter([100,0]), ...
            'theta', DimDegree(0).toRadians() ...
        ) ...
);

%% Define components

comp1 = Component( ...
        'name', 'comp1', ...
        'crossSections', stator1, ...
        'material', MaterialGeneric('name', '10JNEX900'), ...
        'makeSolid', MakeExtrude( ...
            'location', Location3D( ...
                'anchor_xyz', DimMillimeter([0,0,0]), ...
                'rotate_xyz', DimDegree([0,0,0]).toRadians() ...
                ), ...
            'dim_depth', DimMillimeter(15)) ...
        );

    
comp2 = Component( ...
        'name', 'comp2', ...
        'crossSections', stator2, ...
        'material', MaterialGeneric('name', '10JNEX900'), ...
        'makeSolid', MakeExtrude( ...
            'location', Location3D( ...
                'anchor_xyz', DimMillimeter([0,0,0]), ...
                'rotate_xyz', DimDegree([0,0,0]).toRadians() ...
                ), ...
            'dim_depth', DimMillimeter(15)) ...
        );

%% Draw via MagNet

if (DRAW_MAGNET)
    toolMn = MagNet();
    toolMn.open(0,0,true);
    toolMn.setDefaultLengthUnit('millimeters', false);

    comp1.make(toolMn, toolMn);
    comp2.make(toolMn, toolMn);

    toolMn.viewAll();
end

%% Draw via TikZ

if (DRAW_TIKZ)
    toolTikz = TikZ();
    toolTikz.open('output.txt');

    comp1.draw(toolTikz);

    toolTikz.close();
end

%% Draw via JMAG
path = pwd;
fileName = 'test1';

if (DRAW_JMAG)
    toolJd = JMAG();
    toolJd.setVisibility(true);
    toolJd.open();
    comp1.make(toolJd,toolJd);
    comp2.make(toolJd,toolJd);
    toolJd.save(path, fileName);
    toolJd.close();
    delete(toolJd);
end
