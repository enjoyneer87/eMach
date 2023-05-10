
%% Stacklength Coefficient

HDEV1motorcad.stackingFactor.Stacking_FactorStator      =0.97;
HDEV1motorcad.stackingFactor.Stacking_FactorRotor       =0.97;
HDEV1motorcad.stackingFactor.StackingFactor_Magnetics   =2   ;% 0, 1, 2

mcad.SetVariable(strtrim('Stacking_Factor_[Stator]'),HDEV1motorcad.stackingFactor.Stacking_FactorStator   );
mcad.SetVariable(strtrim('Stacking_Factor_[Rotor] '),HDEV1motorcad.stackingFactor.Stacking_FactorRotor    );
mcad.SetVariable(strtrim('StackingFactor_Magnetics'),HDEV1motorcad.stackingFactor.StackingFactor_Magnetics);

%% Demaanetisation Curve Method
HDEV1motorcad.calcMethod.DemagCurveMethod           =1;
mcad.SetVariable(strtrim('DemagCurveMethod'),HDEV1motorcad.calcMethod.DemagCurveMethod);

%% Manufacturing Factors:
HDEV1motorcad.multiplier.ArmatureEWdgMLT_Multiplier         =1;  
HDEV1motorcad.multiplier.ArmatureEWdglnductance_Multiplier  =1;            
HDEV1motorcad.multiplier.Magnet_Br_Multiplier               =0.95;    % 5. Br coefficient

mcad.SetVariable(strtrim('ArmatureEWdgMLT_Multiplier        '),HDEV1motorcad.multiplier.ArmatureEWdgMLT_Multiplier             );
mcad.SetVariable(strtrim('ArmatureEWdgInductance_Multiplier '),HDEV1motorcad.multiplier.ArmatureEWdglnductance_Multiplier      );
mcad.SetVariable(strtrim('Magnet_Br_Multiplier              '),HDEV1motorcad.multiplier.Magnet_Br_Multiplier                   );


%% Length Adjustment Factors
HDEV1motorcad.multiplier.StatorSaturationMultiplier         =0.97;     % 7. Saturation Factor?
HDEV1motorcad.multiplier.RotorSaturationMultiplier          =0.97; 
HDEV1motorcad.multiplier.MagneticAxialLengthMultiplier      =0.98;     


mcad.SetVariable(strtrim('StatorSaturationMultiplier   '),HDEV1motorcad.multiplier.StatorSaturationMultiplier       );
mcad.SetVariable(strtrim('RotorSaturationMultiplier    '),HDEV1motorcad.multiplier.RotorSaturationMultiplier        );
mcad.SetVariable(strtrim('MagneticAxialLengthMultiplier'),HDEV1motorcad.multiplier.MagneticAxialLengthMultiplier    );

%% unsorted
HDEV1motorcad.multiplier.StatorLeakagelnductance_Aux_Multiplier   =1;                 
HDEV1motorcad.multiplier.Magnetizinglnductance_Aux_Multiplier     =1;               
HDEV1motorcad.multiplier.RotorLeakagelnductance_Multiplier        =1;            
HDEV1motorcad.multiplier.StatorlronLossBuildFactor                =1;    
HDEV1motorcad.multiplier.ShaftLossBuildFactor                     =1;
HDEV1motorcad.multiplier.FieldEWdgMLT_Multiplier                  =1;  
HDEV1motorcad.multiplier.ArmatureEWdgMLT_Aux_Multiplier           =1;         
HDEV1motorcad.multiplier.HysteresisLossBuildFactor                =1;    
HDEV1motorcad.multiplier.EddyLossBuildFactor                      =1;
HDEV1motorcad.multiplier.ArmatureEWdglnductance_Aux_Multiplier    =1;                
HDEV1motorcad.multiplier.FluxLinkageMultiplier_Q                  =1;  
HDEV1motorcad.multiplier.FluxLinkageMultiplier_D                  =1;  
HDEV1motorcad.multiplier.IMEquivCircMultipliersDefinition         =1;           
HDEV1motorcad.multiplier.Proximity_Winding_Resistance_Multiplier  =1;  

mcad.SetVariable(strtrim('StatorLeakagelnductance_Aux_Multiplier '),HDEV1motorcad.multiplier.StatorLeakagelnductance_Aux_Multiplier  );
mcad.SetVariable(strtrim('Magnetizinglnductance_Aux_Multiplier   '),HDEV1motorcad.multiplier.Magnetizinglnductance_Aux_Multiplier    );
mcad.SetVariable(strtrim('RotorLeakagelnductance_Multiplier      '),HDEV1motorcad.multiplier.RotorLeakagelnductance_Multiplier       );
mcad.SetVariable(strtrim('StatorlronLossBuildFactor              '),HDEV1motorcad.multiplier.StatorlronLossBuildFactor               );
mcad.SetVariable(strtrim('ShaftLossBuildFactor                   '),HDEV1motorcad.multiplier.ShaftLossBuildFactor                    );
mcad.SetVariable(strtrim('FieldEWdgMLT_Multiplier                '),HDEV1motorcad.multiplier.FieldEWdgMLT_Multiplier                 );
mcad.SetVariable(strtrim('ArmatureEWdgMLT_Aux_Multiplier         '),HDEV1motorcad.multiplier.ArmatureEWdgMLT_Aux_Multiplier          );
mcad.SetVariable(strtrim('HysteresisLossBuildFactor              '),HDEV1motorcad.multiplier.HysteresisLossBuildFactor               );
mcad.SetVariable(strtrim('EddyLossBuildFactor                    '),HDEV1motorcad.multiplier.EddyLossBuildFactor                     );
mcad.SetVariable(strtrim('ArmatureEWdglnductance_Aux_Multiplier  '),HDEV1motorcad.multiplier.ArmatureEWdglnductance_Aux_Multiplier   );
mcad.SetVariable(strtrim('FluxLinkageMultiplier_Q                '),HDEV1motorcad.multiplier.FluxLinkageMultiplier_Q                 );
mcad.SetVariable(strtrim('FluxLinkageMultiplier_D                '),HDEV1motorcad.multiplier.FluxLinkageMultiplier_D                 );
mcad.SetVariable(strtrim('IMEquivCircMultipliersDefinition       '),HDEV1motorcad.multiplier.IMEquivCircMultipliersDefinition        );
mcad.SetVariable(strtrim('Proximity_Winding_Resistance_Multiplier'),HDEV1motorcad.multiplier.Proximity_Winding_Resistance_Multiplier );

%% 
