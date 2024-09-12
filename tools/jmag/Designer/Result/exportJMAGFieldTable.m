function exportFilePath=exportJMAGFieldTable(curStudyObj,selectObj,ResultType,exportFilePath)
            if ResultType=='B'
                ResultType="MagneticFluxDensity";
            elseif ResultType=="force"
                ResultType='Nodalforce';
            elseif ResultType=="J"
                ResultType='CurrentDensity';
            elseif ResultType=="A"
                 ResultType= 'VectorPotential';
            elseif ResultType=="M"
            elseif ResultType=='H'
                 ResultType= 'MagneticFieldStrength';
            elseif ResultType=='p'
                 ResultType= 'Permeance';
            elseif ResultType=="Jloss"
                ResultType="CurrentLossDensityScalar";
            else 
                disp('적절한 데이터를 요청하세요')
            end

            %% Export Table
            parameter = curStudyObj.CreateTableDefinition();
            %  안되면 파이썬 코드로 아래 변경 하기 
            cdList=getCurStudyCondition(curStudyObj);
            if ~any(contains([cdList(:,2)],'MultiSlice'))
                parameter.SetResultType(ResultType ,"<Slice 1>");
                % parameter.SetCoordinate("Global Rectangular")
                parameter.SetCoordinate("Cylindrical")
                parameter.SetComponent(selectObj)
                parameter.SetAllSteps()
                parameter.SetIsShownMinMaxInfo(false)
                parameter.SetIsShownPositionInfo(true)            
                curStudyObj.ExportTable(parameter, exportFilePath, 0);
            end
end


% DemagnetizationRatioUndemagnetized  
% Demagnetization Ratio (Compared to undemagnetized state) 
% 
% 
% Permeance  
% Permeance 
% 
% 
% CoerciveForce  
% Coercive Force (Normalized) 
% 
% 
% NodalForce  
% Nodal Force 
% 
% 
% MagnetostrictiveForce  
% Magnetostrictive Force 
% 
% 
% ContinuousVariable  
% Continuous Variables (Node) 
% 
% 
% DemagnetizationRatioUndemagnetizedTemperature  
% Demagnetization Ratio (Compared to undemagnetized state, temperature dependent) 
% 
% 
% BH  
% Flux Density versus Field Strength 
% 
% 
% MagneticFieldStrength  
% Magnetic Field Strength 
% 
% 
% VectorPotential  
% Magnetic Vector Potential 
% 
% 
% CentrifugalForceGlobalStrain  
% Global Strain (Centrifugal force) 
% 
% 
% CentrifugalForcePrincipalStrain  
% Principal Strain (Centrifugal force) 
% 
% 
% CentrifugalForceMisesStrain  
% Mises Strain (Centrifugal force) 
% 
% 
% PermeanceMin  
% Minimum Permeance by All Steps 
% 
% 
% Deformation  
% Deformation 
% 
% 
% BHLamination  
% Lamination Flux Density versus Field Strength 
% 
% 
% LaminationMagneticFieldStrength  
% Magnetic Field Strength (Lamination) 
% 
% 
% LaminationHysteresisLossDensity  
% Hysteresis Loss Density (Lamination) 
% 
% 
% LaminationCurrentLossDensity  
% Classical Eddy Current Loss Density (Lamination) 
% 
% 
% LaminationEddyCurrentDensity  
% Eddy Current Density (Lamination) 
% 
% 
% LaminationMagneticFluxDensity  
% Magnetic Flux Density (Lamination) 
% 
% 
% InitialMagnetization  
% Initial Magnetization(Normalized) 
% 
% 
% DemagnetizationRatio  
% Demagnetization Ratio (Compared to reference step) 
% 
% 
% MagnetizationRatio  
% Magnetization Ratio 
% 
% 
% TotalIronLossDensityScalar  
% Iron Loss Density 
% 
% 
% HysteresisLossDensityScalar  
% Hysteresis Loss Density 
% 
% 
% CurrentLossDensityScalar  
% Joule Loss Density 
% 
% 
% InitialMagnetizationVector  
% Initial Magnetization Vector 
% 
% 
% CurrentVector  
% Current Vector 
% 
% 
% CentrifugalForceGlobalStress  
% Global Stress (Centrifugal force) 
% 
% 
% PrincipalStress  
% Principal Stress 
% 
% 
% CentrifugalForcePrincipalStress  
% Principal Stress (Centrifugal force) 
% 
% 
% CentrifugalForceMisesStress  
% Mises Stress (Centrifugal force) 
% 
% 
% Displacement  
% Displacement 
% 
% 
% PermeanceMax  
% Maximum Permeance by All Steps 
% 
% 
% Permeability  
% Relative Permeability 
% 
% 
% DifferentialPermeability  
% Differential Permeability 
% 
% 
% SurfaceForceDensity  
% Surface Force Density 
% 
% 
% LorentzForceDensity  
% Lorentz Force Density 
% 
% 
% SurfaceCurrentLossDensityScalar  
% Surface Joule Loss Density 
% 
% 
% CurrentDensity  
% Current Density 
% 
% 
% SurfaceCurrentDensity  
% Surface Current Density 
% 
% 
% MagneticFluxDensity  
% Magnetic Flux Density 
% 
% 
% ResidualFluxDensity  
% Residual Flux Density 
% 
% 
% Magnetization  Magnetization  
