import wave
import contextlib
import librosa

fname = 'p120010.d_object_4.wav'
with contextlib.closing(wave.open(fname,'r')) as f:
    frames = f.getnframes()
    rate = f.getframerate()
    duration = frames / float(rate)
    print(duration.type())

wav_duration = librosa.get_duration(filename=fname)
print(wav_duration)