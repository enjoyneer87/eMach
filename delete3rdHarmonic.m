function B_emf_ph_3f = delete3rdHarmonic(MotorCADEMFph1)

N=length(MotorCADEMFph1);
n=[0:N-1];
X=MotorCADEMFph1;

%%Positive FFT
M=N/2+1;
m=[0:M-1];

%%FFT C
a=(2/N)*X*cos(2*pi*(n')*m/N); %Fourier % a and b coefficients. Note: b0=0 and a0/2 replaces a0.
a(1)=a(1)/2;

b=(2/N)*X*sin(2*pi*(n')*m/N);
B_emf_ph_f=a*cos(2*pi*(m')*n/N)+b*sin(2*pi*(m')*n/N);

%제거 차수
n_e=3;    
a(n_e+1)=0;
b(n_e+1)=0;

%Inverse Fourier
B_emf_ph_3f=a*cos(2*pi*(m')*n/N)+b*sin(2*pi*(m')*n/N);
end