function plot_xdxq(td,data)
%% 1d array
%     plot all
    prop=properties(td);
    for i=1:length(prop)
        ch_prop=td.(char(prop(i))); % data 꺼내면 비효율적이지 않나
        dcheck=size(ch_prop);
    %1열짜리면 meshgrid 형태로 만들기
        if dcheck(1) == 1 & dcheck(2) ~= 1
            disp(strcat(num2str(i),'change to mesh grid'))
            [td.current,td.beta]=meshgrid(td.current, td.beta);
        elseif isempty(td.current_dq)==1
            if td.beta(1)==0 & td.beta(end)==90
            td.current_dq.id=td.current.*cos(deg2rad(td.beta+90));
            td.current_dq.iq=td.current.*sin(deg2rad(td.beta+90));
            elseif td.beta(1)==90 & td.beta(end)==180
            td.current_dq.id=td.current.*cos(deg2rad(td.beta));
            td.current_dq.iq=td.current.*sin(deg2rad(td.beta));
            end
        end
        Wr_test = 2 * pi * td.rpm / 60 * td.p / 2;  
%         Wr_plot = 2 * pi * td.rpm  / 60 * td.p / 2;
        td.flux_linkage.in_d=td.voltage.Vq.*td.current_dq.iq./Wr_test;
        td.flux_linkage.in_q=-td.voltage.Vd-td.Rs.*td.current_dq.id./Wr_test;
    end

%% nd array

%% 
    
    objname=inputname(1); 
%     objname='test'
    if strcmp(data,'flux')
            
            disname='d';
            subplot(2,1,1)
            surf(td.current_dq.id,td.current_dq.iq,td.flux_linkage.in_d,DisplayName=disname);
            hold on
            stem3(td.current_dq.id,td.current_dq.iq,td.flux_linkage.in_d,'DisplayName',disname,"LineStyle","none");

            legend
            grid on
            box on
            ax=gca;
            ax.XLabel.String="id[A]";
            ax.YLabel.String='iq[A]';
            view(2)
            subplot(2,1,2)
            disname='q';
            surf(td.current_dq.id,td.current_dq.iq,td.flux_linkage.in_q,DisplayName=disname);
                        hold on
            stem3(td.current_dq.id,td.current_dq.iq,td.flux_linkage.in_q,'DisplayName',disname,"LineStyle","none");


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

            surf(td.current_dq.id,td.current_dq.iq,td.torque_map,DisplayName=disname);
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
            surf(td.current_dq.id,td.current_dq.iq,td.voltage.Vd,DisplayName=disname);
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
            surf(td.current_dq.id,td.current_dq.iq,td.voltage.Vq,DisplayName=disname);
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
            surf(td.current_dq.id,td.current_dq.iq,td.voltage.Vabs,DisplayName=disname);
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
    

    end

%%  
% %   plot(td.Strain,td.Stress,varargin{:})
%       title(['Stress/Strain plot for Sample',...
%          num2str(td.SampleNumber)])
%       ylabel('Stress (psi)')
%       xlabel('Strain %')
