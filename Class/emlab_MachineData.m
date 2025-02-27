classdef emlab_MachineData < Machinedata
   properties
       
    test_rpm 
    plot_rpm 
    Id
    Iq
    Idmean
    Iqmean
    Result
    res
   end
   properties (Dependent)
    wr_test
    wr_plot
   end
    methods 

   
        function wr_plot=get.wr_plot(emlab_MachineData)
            emlab_MachineData.plot_rpm=emlab_MachineData.test_rpm;
            wr_plot =2 * pi * emlab_MachineData.plot_rpm / 60 * emlab_MachineData.p / 2; %electrical 
        end
    end
end