function P_loss = calcFatamiEddyCurrentLoss(Bfield, w, h, lactive, freqE)
    % 입력:
    % B_r, B_theta - 도체 단면에서의 반경 및 세타 방향 자속 밀도 [TxN 배열]
    % d - 도체 두께
    % w - 도체 폭
    % h - 도체 길이
    % rho - 재료 저항률
    % mu_r - 상대 자기 투과율
    % f - 주파수
    lactive=150
        bc=3.7
    b=5
        hc=1.6
        freqE=rpm2freqE(18000,4)
    % 상수 정의
    mu0  = 4 * pi * 1e-7;  % 진공에서 자기 투과율
    mu_r =1;
    omega = 2 * pi * freqE;    % 각주파수
    elec.T0.resistivity = 1.724E-8;   % 저항값 (옴·미터)
    sigma = 1 / elec.T0.resistivity;  % 전기전도도 (S/m)
    rho   = 1/sigma; 
    delta = sqrt(2 * rho / (mu0 * mu_r * omega));  % 스킨 깊이
    N = 304;  % 도체를 나누는 가상 서브 도체 수
    lactive=mm2m(lactive)
    % 서브 도체의 가로, 세로 분할
    dx = mm2m(bc/N);
    dy = mm2m(hc / N);
    


    NumberL=4


for index=1:2
    EpL(index)=calcEpL(bc*index,b*index,hc*index,NumberL)   
end
    plot(EpL)

B=10
for NumberL=1:4
    for  index=1:2
        testK(NumberL,index)=(B/NumberL/(index)^2)*(sqrt(EpL(index))*(hc*index)/delta).^4
    end
end
figure(2)
    plot(testK)

    sum(testK(:,2).^2)/sum(testK(:,1).^2)
   % plot(testK(2,2)./testK(2,1))
    for b=10:10

      

        (1+2)
for slotIndex=1:4
    B_r     =Bfield(slotIndex).Br      ;
    B_theta =Bfield(slotIndex).Bthetam ;
    BData=table2struct(WireTable(slotIndex,:));
    xVar=BData.fieldxTimeTable.Variables;
    yVar=BData.fieldyTimeTable.Variables;
    xPos=BData.elementCentersTable.x';
    yPos=BData.elementCentersTable.y';
    % 자성 체적에서의 보정계수 η 계산
    total_loss = zeros(size(B_r));
    area= WireTable.elementCentersTable{slotIndex}.area
    area=mmsq2msq(area')
    % for k = 1:240
        % α 보정계수 계산 (Fatami 논문에서 제공)
        %% Juha
    alpha   =calcPeneteDepthInverse(dx,mm2m(b),freqE)    %[1/m]
    coeffixi= alpha*dy; 
    coeffixi = calckXi4EddyLoss(dy,dx,mm2m(b),freqE)

    psiXi =calcProxyEffFun(coeffixi);
    delta             =mm2m(calcSkinDepth(freqE));           % 스킨 깊이 [m]
    [delta_w_prime,~] = calcSkinDepthModi(dx,dy,freqE);  % w' > 나누기 2h
    [delta_h_prime,~] = calcSkinDepthModi(dy,dx,freqE);  % h' > 나누기 2w

    %% eta   
    gamma_w_prime=calcNonDimParaGamma(dx,delta_w_prime/N);    %[m/m]
    gamma_h_prime=calcNonDimParaGamma(dy,delta_h_prime/N);
    %% 
    g2r=calcProxg2(gamma_w_prime, gamma_h_prime)
    g2t=calcProxg2(gamma_h_prime, gamma_w_prime)
    P2Dg2_unitLen= B_r.^2*g2r+ B_theta.^2*g2t;
    P2Dg2        =P2Dg2_unitLen*lactive
    P2Dg2_density =P2Dg2/(dx* dy)/12;
    areaMat=repmat(area,240,1);
    P2Dg2withAcArea=P2Dg2_density.*areaMat
    totalP2Dg2wave=sum(P2Dg2withAcArea,2);
    meanLossP2Dg2=mean(totalP2Dg2wave)
    % P_loss=plot(totalP2Dg2wave)
    Pr=    B_r.^2*g2r
    Pt=    B_theta.^2*g2t
       %% Br modi
   % for timeindex=1:1:len(timeList)
   figure(1)
    for timeindex=3
    scatter3(xPos,yPos,Pr(timeList(timeindex),:),'Marker','v','MarkerEdgeColor','r','MarkerFaceColor',timeColorList{slotIndex},'DisplayName',num2str(3*timeList(timeindex)-3))
    hold on
    % scatter3(xPos,yPos,Pt(timeList(timeindex),:),'MarkerEdgeColor',timeColorList{timeindex},'MarkerFaceColor','none','DisplayName',num2str(3*timeList(timeindex)-3))
    scatter3(xPos,yPos,Pt(timeList(timeindex),:),'Marker','v','MarkerEdgeColor',timeColorList{slotIndex},'MarkerFaceColor','none','DisplayName',num2str(3*timeList(timeindex)-3))
    end
    figure(2)
    for timeindex=3
    scatter3(xPos,yPos,Pr(timeList(timeindex),:)/g2r,'Marker','o','MarkerEdgeColor','k','MarkerFaceColor',timeColorList{slotIndex},'DisplayName',num2str(3*timeList(timeindex)-3))
    hold on
    % scatter3(xPos,yPos,Pt(timeList(timeindex),:),'MarkerEdgeColor',timeColorList{timeindex},'MarkerFaceColor','none','DisplayName',num2str(3*timeList(timeindex)-3))
    scatter3(xPos,yPos,Pt(timeList(timeindex),:)/g2t,'Marker','o','MarkerEdgeColor',timeColorList{slotIndex},'MarkerFaceColor','none','DisplayName',num2str(3*timeList(timeindex)-3))
    end
end
    %%
    varph =calcSkinEffFun(coeffixi,freqE)
    for     zt=1:4
    krk(zt)=varph+(zt)*(zt-1)*psiXi
    end
    plot(krk)
    %% Fatami
    eta = (3 / (4 * alpha^2)) * ((sinh(2 * alpha) - sin(2 * alpha)) / (cosh(2 * alpha) - cos(2 * alpha)));
    
        % 서브 도체 단위의 손실 계산
        % for i = 1:N
            % for j = 1:N
    % 자속 밀도 크기 계산
    % B_eff = sqrt(B_r(i, j)^2 + B_theta(i, j)^2);
    B_effsq= B_r(:,:).^2*dx.^2+ B_theta(:,:).^2*dy.^2;
   
    dPhi_dt =B_effsq*(dx* dy)/12;
    % dPhi_dt =omega.^2*B_effsq*(dx* dy)/12;

    % 유도 전기장 및 전류 밀도 계산
    % dPhi_dt = omega * B_eff.* dx.* dy;  % 자속의 시간 변화율
    E_induced_density = dPhi_dt./(dx* dy);    % 유도 전기장
    J_induced= E_induced_density / rho;        % 전류 밀도
    PDensity_loss_sub = eta *J_induced *lactive;
    % 서브 도체의 손실 (보정계수 적용)
    areaMat=repmat(mmsq2msq(area'),240,1);
    P_loss_sub=PDensity_loss_sub.*areaMat

    total_loss = total_loss + P_loss_sub;
    TimeTotalLoss=sum(total_loss,2)
    meanLoss(b)=mean(TimeTotalLoss)
    end
    P_loss=plot(meanLoss)
                % 총 손실 합산
            % end
        % end
   
    
    % 최종 와전류 손실 반환
end 
