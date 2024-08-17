function selectAirByWorldPosSOD(i_Stator_OD,app)
    % designer = actxserver('designer.Application.210');
    % app = designer;
    %   #matlab으로부터 stator 외경을 입력으로 받아서 공기층에 해당하는 position 반환

    SOD_air = i_Stator_OD/2+0.5;    %[mm]
    SOD_air_cartesian = SOD_air * 0.001; 
    pos_air_xaxis_cart= [SOD_air,0,0]  ;
    SWP_type=3;  % 0x01:Shift    % 0x02:Control   % 0x03:Shift&Control             

    app.View.ShowMesh();
    app.View.ShowAllAirRegions();
    %     #position을 selectWorld 함수에 입력
    app.View().SelectWorldPos(pos_air_xaxis_cart(1),pos_air_xaxis_cart(2),pos_air_xaxis_cart(3),SWP_type);
end