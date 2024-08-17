function HybridSetting=mkMCADHybridACMethodCase(caseIndex)

    switch caseIndex-1
    case 0
        ACLossHighFrequencyScaling_Method   =0;                
        HairpinACLossLocationMethod         =0;        
        HybridACLossMethod                  =0;
    case 1
        ACLossHighFrequencyScaling_Method   =1;                
        HairpinACLossLocationMethod         =0;        
        HybridACLossMethod                  =0;
    case 2
        ACLossHighFrequencyScaling_Method   =0;                
        HairpinACLossLocationMethod         =1;        
        HybridACLossMethod                  =0;
    case 3
        ACLossHighFrequencyScaling_Method   =1;                
        HairpinACLossLocationMethod         =1;        
        HybridACLossMethod                  =0;
    case 4
        ACLossHighFrequencyScaling_Method   =0;                
        HairpinACLossLocationMethod         =0;        
        HybridACLossMethod                  =1;
    case 5
        ACLossHighFrequencyScaling_Method   =1;                
        HairpinACLossLocationMethod         =0;        
        HybridACLossMethod                  =1;
    case 6
        ACLossHighFrequencyScaling_Method   =0;                
        HairpinACLossLocationMethod         =1;        
        HybridACLossMethod                  =1;
    case 7
        ACLossHighFrequencyScaling_Method   =1;                
        HairpinACLossLocationMethod         =1;        
        HybridACLossMethod                  =1;       
    end


    HybridSetting.ACLossHighFrequencyScaling_Method=  ACLossHighFrequencyScaling_Method ;
    HybridSetting.HairpinACLossLocationMethod      =  HairpinACLossLocationMethod       ;
    HybridSetting.HybridACLossMethod               =  HybridACLossMethod                ;
end