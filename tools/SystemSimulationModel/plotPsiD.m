% 함수 1: Psi_d 그래프 그리기
function plotPsiD(Id, Iq, Lamda_ds)
    figure;
    stem3(Id, Iq, Lamda_ds, 'LineStyle', 'none', 'DisplayName', '\lambda_d');
    title('Psi_d');
    xlabel('id');
    ylabel('iq');
    legend;
    box on;
    grid on;
end