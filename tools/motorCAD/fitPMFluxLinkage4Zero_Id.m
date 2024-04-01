function fittedModel = fitPMFluxLinkage4Zero_Id(MCADLinkTable)
    % Is와 CurrentAngle을 사용하여 id, iq 계산

    [idm,iqm]=pkgamma2dq(MCADLinkTable.Is,MCADLinkTable.("Current Angle"));
    
    PMFLuxLinkage=MCADLinkTable.("Flux Linkage D")((difftol(idm,0)));
    iqPM=iqm(difftol(idm,0));
    
    PMFluxTable=table();
    PMFluxTable.PMFLuxLinkage=PMFLuxLinkage;
    PMFluxTable.iqPM         =iqPM;
    
    [~, idx] = unique(PMFluxTable.iqPM, 'stable');
    uniquePMFluxTable = PMFluxTable(idx, :);




    % 데이터에 fitting할 모델 선택 (여기서는 선형 모델 'poly1'을 예로 사용)
    ft = fittype('poly3'); % 'poly2', 'poly3' 등으로 변경 가능
   
    % fit 함수를 사용해 데이터 fitting
    [fittedModel, ~] = fit(uniquePMFluxTable.iqPM, uniquePMFluxTable.PMFLuxLinkage, ft);
    
    % % Fitting 결과 출력
    % disp(fittedModel);
    % disp(gof);
    % 
    % % Fitting 결과와 원래 데이터를 함께 시각화
    % figure;
    % plot(fittedModel, iqPM, PMFLuxLinkage);
    % xlabel('iqPM');
    % ylabel('PMFluxLinkage');
    % title('Fitting of PMFluxLinkage to iqPM');
    % legend('Data', 'Fitted model');
    % % PMFluxLinkageMatrix = repmat(uniquePMFluxTable.PMFLuxLinkage', length(uniquePMFluxTable.iqPM), 1);
    % 
    % %  

    % 업데이트된 flux linkage D 반환
    % fluxDUpdated = fluxD;
end
