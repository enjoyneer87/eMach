% 함수 2: Psi_q 그래프 그리기
function plotPsiQ(Id, Iq, Lamda_qs)
    % figure;
    stem3(Id, Iq, Lamda_qs, 'LineStyle', 'none', 'DisplayName', '\lambda_q');
    title('Psi_q');
    xlabel('id');
    ylabel('iq');
    legend;
end