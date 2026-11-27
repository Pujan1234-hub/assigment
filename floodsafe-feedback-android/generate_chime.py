import math, wave, struct, pathlib
out=pathlib.Path(__file__).parent/'app/src/main/res/raw/feedback_chime.wav'
out.parent.mkdir(parents=True,exist_ok=True)
rate=22050
samples=[]
for i in range(int(rate*.44)):
 t=i/rate
 v=0
 for start,f in [(0,784),(.13,1046.5)]:
  x=t-start
  if 0<=x<.26:
   env=min(1,x/.012)*math.exp(-x*13)*min(1,(.26-x)/.035)
   v+=.19*env*(math.sin(2*math.pi*f*x)+.12*math.sin(2*math.pi*2*f*x))
 samples.append(struct.pack('<h',int(max(-1,min(1,v))*32767)))
with wave.open(str(out),'wb') as f:
 f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate);f.writeframes(b''.join(samples))
