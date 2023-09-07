% 함수 4: 코드 실행 및 결과 출력
% function runPlots(Id, Iq, Lamda_ds, Lamda_qs, torque3_map, torque2_calc, torque_error)
function runPlots(Id, Iq, Lamda_ds, Lamda_qs, torque3_map)

    plotPsiD(Id, Iq, Lamda_ds);
    plotPsiQ(Id, Iq, Lamda_qs);
    % plotTorqueMaps(Id, Iq, torque3_map, torque2_calc, torque_error);
    devPlotTorqueMaps(Id, Iq, torque3_map);

    % disp('그래프 그리기 완료');
end
