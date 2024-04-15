function [LdFitResult, LqFitResult,PMFit2DReulst,FitMCADTable] = fitLdLqMapsFromMCADTable(MCADLinkTable)

    %% 수정필요
    % mcadTable에서 Is와 CurrentAngle 추출
    Is = MCADLinkTable.Is;
    CurrentAngle = MCADLinkTable.("Current Angle");   
    [idm, iqm] = pkgamma2dq(Is, CurrentAngle);
    MCadIdIqTable=MCADLinkTable;
    MCadIdIqTable.idm=idm;
    MCadIdIqTable.iqm=iqm;
   %% gamma=90  fluxD smallest
    PMFitResult=fitPMFluxLinkage4Zero_Id(MCADLinkTable);
    MCadIdIqTable.("PM Flux Linkage")=PMFitResult(iqm);
    % Q축전류만 있는애들은 강제 할당
    MCadIdIqTable.("PM Flux Linkage")(MCadIdIqTable.("Current Angle")==0)=MCadIdIqTable.("Flux Linkage D")(MCadIdIqTable.("Current Angle")==0);
    % 2D Cubic Fit
    [PMFit2DReulst,~,DataSet]=createInterpDataSet(MCadIdIqTable,"PM Flux Linkage");
    % plotFitResult(PMFit2DReulst,DataSet,0)

  
    %% Table 4 Inductance
    nonZeroCurrentIndex=(~difftol(idm,0) &(~difftol(iqm,0)));
    NonZeroITable=table();
    NonZeroITable.Is=MCadIdIqTable.Is(nonZeroCurrentIndex);
    NonZeroITable.("Current Angle")=MCadIdIqTable.("Current Angle")(nonZeroCurrentIndex);
    NonZeroITable.idm=MCadIdIqTable.idm(nonZeroCurrentIndex);
    NonZeroITable.iqm=MCadIdIqTable.iqm(nonZeroCurrentIndex);
    NonZeroITable.("PM Flux Linkage")=MCadIdIqTable.("PM Flux Linkage")(nonZeroCurrentIndex);
    NonZeroITable.("Flux Linkage D")=MCadIdIqTable.("Flux Linkage D")(nonZeroCurrentIndex);
    NonZeroITable.("Flux Linkage Q")=MCadIdIqTable.("Flux Linkage Q")(nonZeroCurrentIndex);

   %% Ld_map과 Lq_map 초기화
    lambda_d  = NonZeroITable.("Flux Linkage D");
    lambda_q  = NonZeroITable.("Flux Linkage Q");% 각 Is, CurrentAngle 조합에 대해 Ld, Lq 계산
    lambda_pm =NonZeroITable.("PM Flux Linkage");
    idmNon=NonZeroITable.idm;
    iqmNon=NonZeroITable.iqm;
    %% 인덕턴스 산정 
    NonZeroITable.Ld_map = (lambda_d - lambda_pm)./ idmNon;
    NonZeroITable.Lq_map = lambda_q ./ iqmNon;

    [LdFitResult,~,~]=createInterpDataSet(NonZeroITable,"Ld_map");
    [LqFitResult,~,~]=createInterpDataSet(NonZeroITable,"Lq_map");

    %% FitTable
    MCadIdIqTable.Ld=LdFitResult(MCadIdIqTable.idm,MCadIdIqTable.iqm)*1000;
    MCadIdIqTable.Lq=LqFitResult(MCadIdIqTable.idm,MCadIdIqTable.iqm)*1000;

    %% Q axis I Only
    lambda_q=MCadIdIqTable.("Flux Linkage Q");
    OnlyQIndex=~difftol(iqm,0)&difftol(idm,0);
    MCadIdIqTable.Lq(OnlyQIndex)=lambda_q(OnlyQIndex)./iqm(OnlyQIndex)*1000;
    %% d axis I Only
    lambda_d=MCadIdIqTable.("Flux Linkage D");
    lambda_pm=MCadIdIqTable.("PM Flux Linkage");
    OnlyDIndex=(difftol(iqm,0)&~difftol(idm,0));
    MCadIdIqTable.Ld(OnlyDIndex)=(lambda_d(OnlyDIndex)-lambda_pm(OnlyDIndex)./iqm(OnlyDIndex))*1000;


    % 부하시 D축 또는 Q축 전류가 0에 가까우면 D/Q축 인덕턴스를 계산할 수 없습니다. 
    % 부하시 위상 진전이 0 또는 90도의 배수(10도 이내)에 가까운 경우 90도의 배수에서 10도 떨어진 
    % 가장 가까운 위상 진전 값에서 별도의 FEA 계산이 수행됩니다.
    % 이 계산 결과는 인덕턴스를 계산하는 데 사용됩니다.
    % 예를 들어 부하시 위상 전위가 5도인 경우 인덕턴스를 계산하기 위해 10도의 위상 전위에서 별도의 FEA 계산이 수행됩니다. 
    % 이 경우 출력 데이터 시트에 보고된 플럭스 연결 및 D/Q 축 전류는 인덕턴스 계산에 사용된 전류와 일치하지 않습니다.
    %%
    FitMCADTable=MCadIdIqTable;
end
