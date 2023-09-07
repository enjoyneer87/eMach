% 함수 3: 토크 맵 및 에러 그래프 그리기
% function plotTorqueMaps(Id, Iq, torque3_map, torque2_calc, torque_error)
function devPlotTorqueMaps(Id, Iq, torque2_calc)

    figure;
    
    % 토크 맵 그리기
    % subplot(1, 2, 1);
    % stem3(Id, Iq, torque3_map, 'LineStyle', 'none', 'DisplayName', 'Torque_{meas}-Map');
    % surf(Id, Iq, torque2_calc, 'LineStyle', 'none', 'DisplayName', 'Torque_{vdvq}-Map');

    hold on;
    stem3(Id, Iq, torque2_calc, 'LineStyle', 'none', 'DisplayName', 'Torque_{vdvq}-Map');
    title('Torque-[Nm]');
    xlabel('id');
    ylabel('iq');
    legend;
    % 
    % % 토크 에러 그래프 그리기
    % subplot(1, 2, 2);
    % surf(Id, Iq, torque_error, 'LineStyle', 'none', 'DisplayName', 'Error_{meas-vdvq}-Map');
    % title('Torque error-[Nm]');
    % xlabel('id');
    % ylabel('iq');
    % hold on;
    % stem3(Id, Iq, torque_error, 'LineStyle', 'none', 'DisplayName', 'Error_{meas-vdvq}-Map');
    % hold on;
    % stem3(Id, Iq, Input_torque1_from, 'LineStyle', 'none', 'DisplayName', 'Input Torque');
    % legend;
end