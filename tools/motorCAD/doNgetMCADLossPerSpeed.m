function MCADResultSet=doNgetMCADLossPerSpeed(mcad,speedList,HybridSetting)
        % 속도별로 추출
        ACLossHighFrequencyScaling_Method= HybridSetting.ACLossHighFrequencyScaling_Method ;
        HairpinACLossLocationMethod      = HybridSetting.HairpinACLossLocationMethod       ;
        HybridACLossMethod               = HybridSetting.HybridACLossMethod                ;

        %%
        for speedIndex = 1:length(speedList)
            % MCAD 설정
            mcad(1).SetVariable('ACLossHighFrequencyScaling_Method', ACLossHighFrequencyScaling_Method);
            mcad(1).SetVariable('HairpinACLossLocationMethod', HairpinACLossLocationMethod);
            mcad(1).SetVariable('HybridACLossMethod', HybridACLossMethod);
            
            % 속도 설정 및 시뮬레이션 실행
            mcad(1).SetVariable('ShaftSpeed', speedList(speedIndex));
            mcad(1).DoMagneticCalculation;
            
            % 시뮬레이션 결과 저장
            MCADResultSet.ACLossHighFrequencyScaling_Method = ACLossHighFrequencyScaling_Method;
            MCADResultSet.HairpinACLossLocationMethod       = HairpinACLossLocationMethod;
            MCADResultSet.HybridACLossMethod                = HybridACLossMethod;
            MCADResultSet.Speed(speedIndex)                 = speedList(speedIndex);
            %% loadMCADSimulData -GraphData / ResultTable
            MCADResultSet.EmagResult(speedIndex)            =loadMCADSimulData(mcad(1)); 
            %% PostCalc with WaveForm
            WaveForm       =MCADResultSet.EmagResult(speedIndex).Wave;
            BWave_Conductor=[WaveForm.BCoductor{:}]';
            
            for cIdx=1:1:height(BWave_Conductor)/2
                figure(cIdx)
                if contains(BWave_Conductor(2*cIdx-1).DataName,'L_')
                BleftTable  =BWave_Conductor(2*cIdx-1).dataTable   ;
                Bleft       =BleftTable.GraphValue;
                %
                symmetryNThermalFactor=(1 / (1 + alpha * (T - T0)))*double(slotNumber)/2*HybridAdjustmentFactor_ACLosses;
                calc.PacLeftFromWaveB{cIdx}  =    (mm2m(la)*mm2m(Cuboid_Width)*(mm2m(Cuboid_Height))^3*sigma * (omegaE .*Bleft ).^2/divCoeffi)*symmetryNThermalFactor*2;    
                % PacLeft_WaveCalc{cIdx}    = (mm2m(la) * mm2m(Copper_Width) * (mm2m(Copper_Height))^3 * sigma * (omegaE .* Bleft).^2 ./ 12) .*symmetryNThermalFactor ;
                % plot(BleftTable.Angle,PacLeft_WaveCalc{cIdx} )
                hold on
                plot(BleftTable.Angle,calc.PacLeftFromWaveB{cIdx})
                end
                if contains(BWave_Conductor(2*cIdx).DataName,'R_')
                BRightTable =BWave_Conductor(2*cIdx).dataTable ;
                BRight      =BRightTable.GraphValue;
                %
                calc.PacRightFromWaveB{cIdx} =    (mm2m(la)*mm2m(Cuboid_Width)*(mm2m(Cuboid_Height))^3*sigma*  (omegaE .*BRight).^2/divCoeffi) *symmetryNThermalFactor*2 ;
                % PacRight_WaveCalc{cIdx}   = (mm2m(la) * mm2m(Copper_Width) * (mm2m(Copper_Height))^3 * sigma * (omegaE .* BRight).^2 / 12) .* (1 / (1 + alpha * (T - T0))) .*double(slotNumber)./2.*HybridAdjustmentFactor_ACLosses ;
                % plot(BRightTable.Angle,PacRight_WaveCalc{cIdx} )
                plot(BleftTable.Angle,calc.PacRightFromWaveB{cIdx})
                end             
                % Pac_WaveCalc{cIdx}        = (mm2m(la) * mm2m(Copper_Width) * (mm2m(Copper_Height))^3 * sigma * (omegaE .* B).^2 / 12) * (1 / (1 + alpha * (T - T0)))      .*double(slotNumber).*HybridAdjustmentFactor_ACLosses ;
            end
            %% Comparison
            %% Check There is Same Type Figure
            FigureData.PlotType='Comparison';
            [~,NofConductor]=mcad.GetVariable('WindingLayers');
            NofConductor=double(NofConductor);
            ConductorNameListCell=mkNameListConductorACLoss(NofConductor);
            DataNameList={};

            %%
            for cIdx=1:1:height(BWave_Conductor)/2
                figure(cIdx)
                opData.Wave.ACLossCoductor{(2*cIdx-1)}= plotMCADEmagCalc(ConductorNameListCell{2*cIdx-1}, mcad,FigureData);
                %Name
                tempName=strrep([ConductorNameListCell{(2*cIdx-1)}],'AC','');
                DataNameList{1}=strrep(tempName,'Loss','');
                % addName
                opData.Wave.ACLossCoductor{((2*cIdx-1))}.DataName =DataNameList{1};
                hold on
                opData.Wave.ACLossCoductor{2*cIdx}= plotMCADEmagCalc(ConductorNameListCell{2*cIdx}, mcad,FigureData);
                %Name
                tempName=strrep([ConductorNameListCell{2*cIdx}],'AC','');
                DataNameList{2}=strrep(tempName,'Loss','');
                % addName
                opData.Wave.ACLossCoductor{2*cIdx}.DataName =DataNameList{2};
                if strcmp(FigureData.PlotType,'Comparison')
                tempName=strrep([ConductorNameListCell{(2*cIdx-1)}],'AC','');
                DataNameList{3}=strrep(tempName,'Loss','');
                tempName=strrep([ConductorNameListCell{2*cIdx}],'AC','');
                DataNameList{4}=strrep(tempName,'Loss','');
                %    DataNameList{3}=strrep([ConductorNameListCell{CuIndex}],'FluxDensity','');
                %    DataNameList{4}=strrep([ConductorNameListCell{CuIndex+1}],'FluxDensity','');
                end
                % legend(DataNameList);
                hold on
            end


            % plot(MCADResultSet.EmagResult(speedIndex).Wave.ACLossCoductor{1}.dataTable.GraphValue)
             MCADResultSet.EmagResult(speedIndex)
            %% 여기에 다른 필요한 결과 데이터를 저장하는 코드 추가 % Graph Data/ResultTable
            MCADResultSet.CalchybridACLoss(speedIndex)       =devCalcHybridACLossModelwithSlotB(mcad(1));
            % index = index + 1;
        end


end