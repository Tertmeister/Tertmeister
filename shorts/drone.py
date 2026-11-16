import sys, numpy as np, wave
sr=44100; dur=float(sys.argv[2]); n=int(sr*dur); t=np.arange(n)/sr
rng=np.random.default_rng(3)
def pad(f, det=0.15):
    return sum(np.sin(2*np.pi*(f*(1+d*det/100))*t + rng.random()*6) for d in (-1,0,1))/3
# D minor drone: D2, A2, D3, F3 (faint)
x = 0.5*pad(73.42) + 0.35*pad(110.0) + 0.25*pad(146.83) + 0.12*pad(174.61)*(0.5+0.5*np.sin(2*np.pi*t/13))
x *= 0.75 + 0.25*np.sin(2*np.pi*t/9.0)
# wind: low-passed noise with slow swells
w = rng.normal(0,1,n)
k = np.exp(-np.arange(200)/40); k/=k.sum()
w = np.convolve(w,k,'same'); w = np.convolve(w,k,'same')
w *= (0.4+0.6*(0.5+0.5*np.sin(2*np.pi*t/7.3+1))**2)
x = x/np.abs(x).max()*0.6 + w/np.abs(w).max()*0.35
fade = np.minimum(1, t/2.0) * np.minimum(1, (dur-t)/2.0)
x = x*fade; x = x/np.abs(x).max()*0.9
st = np.stack([x, np.roll(x, 300)],1)
with wave.open(sys.argv[1],'wb') as f:
    f.setnchannels(2); f.setsampwidth(2); f.setframerate(sr); f.writeframes((st*32767).astype(np.int16).tobytes())
