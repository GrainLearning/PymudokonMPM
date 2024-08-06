
p(s1,s2,s3)=(s1+s2+s3)/3.
sdev(s1,s2,s3)=sqrt((s1-s2)**2+(s1-s3)**2+(s2-s3)**2)/sqrt(6)
sdevmm(s1,s2,s3)=(s1-s3)/2.
eV(s1,s2,s3)=(s1+s2+s3)/3.
edev(s1,s2,s3)=sqrt((s1-s2)**2+(s1-s3)**2+(s2-s3)**2)/sqrt(6)

eabs(e1,e2)=sqrt(e1**2+e2**2)/2
sabs(s1,s2)=sqrt(s1**2+s2**2)

#=======================================================================
# NEW SHORT VERSION
#
mu0=0.15 
muinf=0.42    # just a guess ??? to be checked! 
I01=0.06
I0sigma=I01
p0sigma=40
p00sigma=p0sigma*mu0**2
#
muIp0(I,p)=( mu0 + (muinf-mu0)/(1.+I0sigma/I) ) 
#
muIp(I,p)=( mu0 + (muinf-mu0)/(1.+I0sigma/I) ) * (1.-(p/p00sigma)**0.5)
#muIp(I,p)=( mu0 + (muinf-mu0)/(1.+I0sigma/I) ) * exp(-(p/p00sigma)**0.5)

print "=> muIp(I,p)=( mu0 + (muinf-mu0)/(1.+I0sigma/I) ) * (1.-(p/p00sigma)**0.5) "
#print "=> muIp(I,p)=( mu0 + (muinf-mu0)/(1.+I0sigma/I) ) * exp(-(p/p00sigma)**0.5) "
print "mu_0, mu_inf, I^0_sigma, p^00_sigma"
print mu0, muinf, I0sigma, p00sigma

# v.6 - small I and p corrections by Sudeshna
Istarq=5e-5
alphaq=0.5
a_g=0.35
p_g0=2.0
muIpq(I,p) = muIp(I,p) * (1.-exp(-(I/Istarq)**alphaq))
muIpg(I,p,p_g) = muIp(I,p) * (1.-a_g*exp(-p_g/p_g0)) 
muIpgq(I,p,p_g) = muIp(I,p) * (1.-a_g*exp(-p_g/p_g0)) * (1.-exp(-(I/Istarq)**alphaq))
#
print "=> muIpq(I,p,p_g) = muIp(I,p) * (1-exp(-(I/Istarq)**alphaq))"
print "=> muIpgq(I,p,p_g) = muIp(I,p) * (1-a_g*exp(-p_g/p_g0)) * (1-exp(-(I/Istarq)**alphaq))"
print "a_g, p_g0, I_starq, alphaq "
print a_g, p_g0, Istarq, alphaq

#
# ... and density with I and pressure dependence
phic_e=0.649
pnux_e=0.33
Ip0x_e=0.85
#
phic=0.649
pnux=0.33
Ip0x=0.85

phix(I,p)=phic * (1.+p/pnux) * (1.-(I/Ip0x))
# OLD: 
# phix(I,p)=phic +p/pnux -(I/Ip0x)
# NEWNEW:
# phix(I,p)=phic * exp(p/pnux) * exp(-(I/Ip0x))
phix_e(I,p)=phic_e * exp(p/pnux_e) * exp(-(I/Ip0x_e))

print "phix(I,p)=phic*(1.+p/pnux)*(1.-(I/Ip0x))"
print "phic, pnux, Ip0x"
print phic, pnux, Ip0x

p_0=0.042
Ip_0=0.01
nuc=0.64
pe(nu) = nu>=nuc ? p_0*nu*log(nu/nuc) : 0
p(nu,I) = pe(nu) + I/Ip_0 
print "p(nu,I) = p_0 * nu * log(nu/nuc) + I/Ip_0"
print "nuc, p_0, Ip_0 "
print  nuc, p_0, Ip_0

### not used ###
fphix(I,p,pnux,Ip0x)=phic*(1.+p/pnux)*(1.-(I/Ip0x))

