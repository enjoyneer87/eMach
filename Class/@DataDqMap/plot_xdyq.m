function td=plot_xdyq(td,data)
%% 1d array
%     plot all
    propertiesData=properties(td);
    for i=1:length(propertiesData)
        ch_prop=td.(char(propertiesData(i))); % data 꺼내면 비효율적이지 않나
        dcheck=size(ch_prop);
    %1열짜리면 meshgrid 형태로 만들기
        if dcheck(1) == 1 & dcheck(2) ~= 1
            disp(strcat(num2str(i),'change to mesh grid'))
            [td.current,td.beta]=meshgrid(td.current, td.beta);
        elseif isempty(td.current_dq_map)==1
            if td.beta(1)==0 & td.beta(end)==90
            td.current_dq_map.id=td.current.*cos(deg2rad(td.beta+90));
            td.current_dq_map.iq=td.current.*sin(deg2rad(td.beta+90));
            elseif td.beta(1)==90 & td.beta(end)==180
            td.current_dq_map.id=td.current.*cos(deg2rad(td.beta));
            td.current_dq_map.iq=td.current.*sin(deg2rad(td.beta));
            end
        end
        Wr_test = 2 * pi * td.rpm / 60 * td.p / 2;  
%         Wr_plot = 2 * pi * td.rpm  / 60 * td.p / 2;
%         td.flux_linkage_map.in_d=td.voltage.Vq.*td.current_dq_map.iq./Wr_test;
%         td.flux_linkage_map.in_q=-td.voltage.Vd-td.Rs.*td.current_dq_map.id./Wr_test;
    end
        
       %1열짜리면 meshgrid 형태로 만들기
    sizeIdq=size(td.current_dq_map.id);
    if sizeIdq(1) == 1 & sizeIdq(2) ~= 1
         [td.current_dq_map.id,td.current_dq_map.iq]=meshgrid(td.current_dq_map.id,td.current_dq_map.iq)

    end
%% nd array

%% average map
if ndims(td.flux_linkage_map.in_d)==2
%     objname=inputname(1); 
    objname='test'
    if strcmp(data,'flux')
            
            disname='d';
            subplot(2,1,1)
            surf(td.current_dq_map.id,td.current_dq_map.iq,td.flux_linkage_map.in_d,DisplayName=disname);
            hold on
            stem3(td.current_dq_map.id,td.current_dq_map.iq,td.flux_linkage_map.in_d,'DisplayName',disname,"LineStyle","none");

            legend
            grid on
            box on
            ax=gca;
            ax.XLabel.String="id[A]";
            ax.YLabel.String='iq[A]';
            view(2)
            subplot(2,1,2)
            disname='q';
            surf(td.current_dq_map.id,td.current_dq_map.iq,td.flux_linkage_map.in_q,DisplayName=disname);
                        hold on
            stem3(td.current_dq_map.id,td.current_dq_map.iq,td.flux_linkage_map.in_q,'DisplayName',disname,"LineStyle","none");


            legend
            grid on
            box on
            ax=gca;
            ax.XLabel.String="id[A]";
            ax.YLabel.String='iq[A]';
            view(2)
            title(data)
    elseif  strcmp(data,'torque')

        for i=width(td.beta):-1:1
            disname=strcat(mat2str(td.current(1,i)),'[A]_{pk}'," - ",objname);

            surf(td.current_dq_map.id,td.current_dq_map.iq,td.torque_map,DisplayName=disname);
            hold on
            legend
            grid on
            box on
            ax=gca;
            ax.XLabel.String="id[A]";
            ax.YLabel.String='iq[A]';
            view(2)
            title(data)
        end
    elseif strcmp(data,'voltage')
%         for i=width(td.rpm):-1:1
            %Vd
%             disname=strcat(mat2str(td.current(1,i)),'[A]_{pk}'," - ",objname);
            disname='Vd'
            subplot(4,2,[1 3])
            surf(td.current_dq_map.id,td.current_dq_map.iq,td.voltage.Vd,DisplayName=disname);
            hold on
            legend
            grid on
            box on
            ax=gca;
            ax.XLabel.String="id[A]";
            ax.YLabel.String='iq[A]';
            view(2)
            % Vq
            disname='Vq'

            subplot(4,2,[2 4])
            surf(td.current_dq_map.id,td.current_dq_map.iq,td.voltage.Vq,DisplayName=disname);
            hold on
            legend
            grid on
            box on
            ax=gca;
            ax.XLabel.String="id[A]";
            ax.YLabel.String='iq[A]';
            view(2)
            %Vabs
            disname='Vabs'
            subplot(4,2,[5 7])
            surf(td.current_dq_map.id,td.current_dq_map.iq,td.voltage.Vabs,DisplayName=disname);
            hold on
            legend
            grid on
            box on
            ax=gca;
            ax.XLabel.String="id[A]";
            ax.YLabel.String='iq[A]';
            view(2)
            title(data)
            %Vfund
%         end
    end

%% varying rotor position
elseif ndims(td.flux_linkage_map.in_d)==3

sizeFluxMap=size(td.flux_linkage_map.in_d)
check_flag = 0;

for j=1:sizeFluxMap(3)
    
    clf
    d=td.flux_linkage_map.in_d(:,:,j);
    q=td.flux_linkage_map.in_q(:,:,j);    
    subplot(1,2,1)
    surf(td.current_dq_map.id,td.current_dq_map.iq,d)
    ylabel('iq');
    xlabel('id');
    title('\lambda_d');
    dim = [.5 .5 .3 .3];
    str=strcat('Rotor position=', num2str(td.angleVec(j)), 'deg');
    annotation('textbox',dim,'String',str,'FitBoxToText','on');
    colorbar 
    subplot(1,2,2)
    surf(td.current_dq_map.id,td.current_dq_map.iq,q)
    ylabel('iq');
    xlabel('id');
    title('\lambda_q');
    filename = 'fluxdQ.gif';
    colorbar
    drawnow
    Flux_map= getframe(gcf); 
    
    im = frame2im(Flux_map);
    [imind,cm] = rgb2ind(im,256);


    if check_flag == 0
        imwrite(imind,cm,filename,'gif','LoopCount',inf);
        check_flag = 1;
    else
        imwrite(imind,cm,filename,'gif','WriteMode','append');
    end


end



end

end
