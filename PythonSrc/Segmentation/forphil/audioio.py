#! /usr/bin/env python
import os, sys, tempfile, string ,time
from numpy import *
import numpy as N



#wrappers for audio io
#uses pyaudiolab for non-mp3 and command-line tools for mp3



#makes filenames safe for calling using os.popen(cmd)
def slashify(fname) :
    s_fname=string.replace(fname," ","\ ")
    s_fname=string.replace(s_fname,"\'","\\'")
    s_fname=string.replace(s_fname,"\"","\\\"")
    s_fname=string.replace(s_fname,"(","\(")
    s_fname=string.replace(s_fname,")","\)")
    s_fname=string.replace(s_fname,"&","\&")
    s_fname=string.replace(s_fname,";","\;")
    s_fname=string.replace(s_fname,"$","\$")
    s_fname=string.replace(s_fname,"`","\`")
    s_fname=string.replace(s_fname,",","\,")
    s_fname=string.replace(s_fname,"-","\-")
    return s_fname


#read from a process
def command_with_output(cmd):
    if not type(cmd) == unicode :
        cmd = unicode(cmd,'utf-8')
    #should this be a part of slashify or command_with_output?
    #if sys.platform=='darwin' :
    #    cmd = unicodedata.normalize('NFC',cmd)
    child = os.popen(cmd.encode('utf-8'))
    data = child.read()
    err = child.close()
    return data


def pyaudioread_wrapper(fn,tlast=-1,fs_target=-1,stats_only=False) :
    #internal use only
    try:
        import pyaudiolab as P
    except :
        import scikits.audiolab as P

    a=P.sndfile(fn)
    fs=a.get_samplerate()

    if stats_only :
        #return len_sec,fs,t_count triple
        return (int(round(float(a.get_nframes())/fs)),fs,a.get_channels())
    
    if tlast==-1 :
        fcount=a.get_nframes()
    else :
        fcount = min(a.get_nframes(),int(fs*tlast+.5))
        #print 'reading in first',fcount,'of',a.get_nframes()
        
    if fs_target>0 and not fs_target==fs :
        import pysamplerate as P
        #print 'Resampling'
        x=P.resample(a.read_frames(fcount),float(fs_target)/float(fs),P.converter_format('sinc_fastest'),verbose=False)
        fs=fs_target
    else :
        x=a.read_frames(fcount)
    a.close()
    return (x,fs)



def audiowrite(dat,fn,fs) :
    #internal use only
    try:
        import pyaudiolab as P
    except :
        import scikits.audiolab as P

    P.wavwrite(dat,fn,fs)

def audioread(fn,mono=False,tlast=-1,fs_target=-1,stripzeros='none',stats_only=False,decoder='madplay') :
    #Reads several formats of audio
    #Flags:
    #         mono: yields a mono sample
    #        tlast: is desired last sample in sec
    #    fs_target: is a target fs. resampling / decimation will be used to get the target rate
    #  stripzeros:  removes near-zero-values from beginning and/or end of signal
    #               values can be 'none','both','leading','trailing'
    #   stats_only: will return triple (n_sec,fs,num_channels) of song, ignoring stripzeros, fs_target and t_last
    #               that is, we get the size and fs of the song as written on disk, not what we would get from
    #               reading using audioread and supplied params.  Note we get n_sec not n_samples because that
    #               is faster.  I don't think we know number of samples until decoding
    #     decoder:  pymad, madplay, mpg123; default is madplay because it uses same decoder as pymad but supports downsampling



    if not os.path.exists(fn) :
        raise IOError ('File %s not found' %fn )
    stub=fn.lower().split('.')
    stub=stub[len(stub)-1]
    
    #print 'Decoder is',decoder
    
    if stub=='mp3' :
        #if pymad it is missing, default to mpg123
        if decoder=='pymad' :
            try :
                import mad
            except :
                decoder='mpg123'
        
        #load stats by default using mad. otherwise try mp3info
        try :
            import mad

            #here we work around an oddity of mad that sometimes the sampling rate is wrong for the very first frame
            #this may be normal behavior but it seems odd to me. So we read once and then reset
            mf=mad.MadFile(fn)
            try :
                mf.read()
                mf.seek_time(0)
            except :
                pass
            fs=mf.samplerate()

            if mf.mode() == mad.MODE_SINGLE_CHANNEL:
                channel_count=1
                #print "single channel"
            elif mf.mode() == mad.MODE_DUAL_CHANNEL:
                channel_count=2;
                #print "dual channel"
            elif mf.mode() == mad.MODE_JOINT_STEREO:
                channel_count=2;
                #print "joint (MS/intensity) stereo"
            elif mf.mode() == mad.MODE_STEREO:
                channel_count=2;
                #print "normal L/R stereo"
            else:
                #print "unexpected mode value"
                channel_count=1
                
            secs=int(mf.total_time()/1000.0)
            #print fn,'Total time',mf.total_time(),'fs',fs
        except :
            print 'Python mad library not loaded. Trying to use mp3info'
            try :
                cmd = 'mp3info -p \"%%Q %%S %%o\" %s' % slashify(fn)
                data=command_with_output(cmd)
                vals = data.split(' ')
                fs=int(vals[0])
                secs=int(vals[1])
                stereo_mono_mode=string.join(vals[2:len(vals)])
                channel_count=1
                if stereo_mono_mode.find('stereo')>=0:
                    channel_count=2
            except :
                raise ImportError, "You must load the python mad library or have mp3info available"


        if stats_only :
            return (secs,fs,channel_count)


        #mono and downsampling don't work with mpg321
        if decoder=='mpg123' :
            print 'Warning mpg123 decoder doe not work very well compared to madplay'
            cmd=decoder
            if mono:
                cmd = '%s -m' % (cmd)
                channel_count=1 #force the channel count to be 1
            if not fs_target==-1 :
                #mpg123 downsamples by 2:1 or 4:1
                fsratio = float(fs)/float(fs_target)
                if fsratio >= 4.0 :
                    cmd = '%s -%i' % (cmd,4)
                    fs/=4
                elif fsratio >=2.0 :
                    cmd = '%s -%i' % (cmd,2)
                    fs/=2
            cmd = '%s -q -s %s' % (cmd,slashify(fn))
            data=command_with_output(cmd)
            x = N.zeros(len(data)/2,'float')
            x[:] = N.fromstring(data,'short') / float(32768) 
                                    
            if channel_count>1 :
                x=x.reshape(-1,channel_count)

        elif decoder=='madplay':
            

            import tempfile
            cmd=decoder
            
            #0.000357536896089
  
            if not fs_target==-1 :
                #madplay downsamples by 2:1
                #but the downsampling is low quality. maybe don't use it?
                fsratio = float(fs)/float(fs_target)
                if fsratio >=2.0 :
                    cmd = '%s --downsample' % (cmd)
                    fs/=2

            if False: #use temporary file on disk
                (tmpfh,tmpfn)=tempfile.mkstemp()
                cmd = '%s -Q --output=raw:%s %s' % (cmd,tmpfn,slashify(fn))
                #print 'Calling ',cmd
                tic=time.time()
                command_with_output(cmd)
                tmpfh=open(tmpfn,'r')
                data = N.fromfile(tmpfh,N.short)
                print 'Done calling',time.time()-tic
            else :  #use stdout
                cmd = '%s -Q --output=raw:- %s' % (cmd,slashify(fn))
                #print 'Running',cmd
                data=command_with_output(cmd)
                data=N.fromstring(data,'short')
           
            x = N.zeros(len(data),'float')
            x[:] = data/float(32768)
            #print 'Loaded',N.shape(x),'with mean',N.mean(x)
            #here we override the channel count from above using a time test
            #this is because some mp3s seem to return SINGLE_CHANNEL when they are in fact stereo mp3s
            if float(fs)*secs>0 :
                test_channel_count = int(round(len(x)/(float(fs)*secs)))
                if test_channel_count<>channel_count :
                    print 'audioio.py: Overriding channel_count',channel_count,'with',test_channel_count,'for',fn
                    channel_count=test_channel_count
            if channel_count>1 :
                x=x.reshape(-1,channel_count)
        elif decoder=='pymad' :
            samps_per_channel = (mf.samplerate() * mf.total_time()) /1000.0
            channels=mf.mode()
            samples = samps_per_channel * channels
            x = N.zeros(((samps_per_channel+fs)*channels,1))  #we store 1 second at end of song
            st=0
            while True :
                buf = mf.read()
                if buf is None :
                    break
                bsamps=len(buf)/2
                if st+bsamps>samples :
                    break
                x[st:st+bsamps,0]=N.fromstring(buf,'short') / float(32768)
                st+=bsamps
            x=x.reshape(-1,2)
            x=x[0:st/2,:]    
        else:
            print 'audioio.py: unknown decoder',decoder
            sys.exit(0)

        if fs_target>0 and not fs==fs_target :
            #print 'audioio : resampling from',fs,'to',fs_target,'on x len',N.shape(x),
            import pysamplerate as P
            x=P.resample(x,float(fs_target)/float(fs),P.converter_format('sinc_fastest'),verbose=False)
            fs=fs_target



        if tlast>0 :
            if len(N.shape(x))==1 :
                x=x[0:tlast*float(fs)]
            else :
                x=x[0:tlast*float(fs),:]


                
    elif stub=='mid' or stub=='midi' :
        import pymidi as P
        mf=P.MidiFile(fn)
        if fs_target==-1 :
            fs_target=1000    
        (x,fs)=mf.timeseries(fs=fs_target)
        
        
    else :
        decoder='wav'
        if stats_only :
            return pyaudioread_wrapper(fn,tlast=tlast,fs_target=fs_target,stats_only=stats_only)
        (x,fs)= pyaudioread_wrapper(fn,tlast=tlast,fs_target=fs_target)

    
    if mono and len(N.shape(x))>1 :
        x=N.mean(x,1)
        #could this cause problems?
        #x=x.flatten()
        

    


    #now remove zeros
    assert(len(N.shape(x))<=2)  #better be stereo or mono!

    if not (stripzeros=='leading' or stripzeros=='trailing' or stripzeros=='both' or stripzeros=='none') :
        print 'Invalid value for stripzeros; must be leading, trailing, both or none'
        print 'Setting to none'
        stripzeros='none'

    if not stripzeros=='none' :
        (x,svals) = strip_zeros(x,stripzeros)

    #print 'Loaded',fn,'length',len(x)/float(fs)



    if stripzeros=='none' :
        return (x,fs,[])
    else :
        return (x,fs,svals)
    

def strip_zeros(x,stripzeros='both',lim=.01) :
    leading_samples=0
    trailing_samples=0
    if len(x)==0 :
        return (x,N.zeros(2))
    if not stripzeros=='none':
        #prepare mono abs sequence for checking zerovals
        if len(N.shape(x))>1 :
            xAbs=abs(N.mean(x,1))
        else:
            xAbs=abs(x)
         
        #be sure our sequence is not all zeros (or <lim)
        #we will sample from the middle of the file K times. If they're all 0
        #we will take the max. This way we won't always take the max, which is expensive!
        if len(x)>100 :
            midIdx=int(len(x)/2)
            takeMax=True
            for i in range(midIdx,midIdx+10) :
                if xAbs[midIdx]>=lim :
                    takeMax=False
                    break
            if takeMax :
                if xAbs.max()<lim :
                    return([],(len(x),0))
        
    if stripzeros=='leading' or stripzeros=='both' :
        leading_samples=0
        while xAbs[leading_samples]<lim and leading_samples<(len(xAbs)-1) :
            leading_samples+=1
        if leading_samples>0:
            if len(N.shape(x))==2 :
                x=x[leading_samples:,:]  #stereo                
            else:
                x=x[leading_samples:]    #mono
            xAbs=xAbs[leading_samples:]    #xAbs is mono

    if stripzeros=='trailing' or stripzeros=='both' :
        trailing_idx=len(xAbs)-1
        while xAbs[trailing_idx]<lim and trailing_idx>0 :
            trailing_idx-=1
        if trailing_idx<len(xAbs)-1:
            if len(N.shape(x))==2 :
                x=x[0:trailing_idx,:]  #stereo
            else:
                x=x[0:trailing_idx]    #mono
        trailing_samples=len(xAbs)-trailing_idx

    svals=N.zeros(2)
    svals[0]=leading_samples
    svals[1]=trailing_samples
    return (x,svals)

def get_secstr(secs):
    if secs==-1 :
        return '??:??'
    else :
        min=int(secs/60)
        sec=secs-(min*60)
        return '%s:%s' % (str(min).zfill(2),str(sec).zfill(2))

def get_secs_and_stripzero_secs(mp3,fs=11025,decoder='madplay') :
    #get length of signal (sec) and length with zeros stripped (zsec)
    #try :
    (x,fs,stripvals)=audioread(mp3,fs_target=fs,stripzeros='both',stats_only=False,decoder=decoder)
    zsec=0
    sec=0
    if fs>0 :
        zsec=float(len(x)/float(fs))
        sec=float(zsec + sum(stripvals)/float(fs))
    #except :
    #    import traceback
    #    traceback.print_exc()
    #    #sys.exit(0)
    #    sec=-1.0
    #    zsec=-1.0
    return (sec,zsec)


def die_with_usage() :
    print 'audioio.py [flags] file'
    print 'This is mainly a library function to be used by other code'
    print 'Flags:'
    print ' -decoder <decoder> where decoder is mpg123 (default), madplayer or pymad'
    print ' -testdecoders will compare decoders'
    print ' -mono will force mono'
    print ' -fs <rate> sets target sample rate'
    print 'Arguments :'
    print '  <file> is a valid mp3, wave or au file'
    sys.exit(0)
    
if __name__=='__main__' :
    import time

    if len(sys.argv)<2 :
        die_with_usage()

    testdecoders=False
    decoder='madplay'
    fs_target=-1
    mono=False
    while True :
        if sys.argv[1]=='-decoder' :
            decoder=sys.argv[2]
            sys.argv.pop(1)
        elif sys.argv[1]=='-fs' :
            fs_target=int(sys.argv[2])
            sys.argv.pop(1)
        elif sys.argv[1]=='-testdecoders' :
            testdecoders=True
        elif sys.argv[1]=='-mono' :
            mono=True
        else :
            break
        sys.argv.pop(1)
        

    
    fn=sys.argv[1]



    import pylab as P

    if testdecoders :

        import mp3_eyeD3
        eyed3_secs=mp3_eyeD3.mp3_gettime(fn)
        tic=time.time()
        (x1,fs1,ignore)=audioread(fn,decoder='mpg123',fs_target=fs_target,mono=False)
        time1=time.time()-tic

        #print 'Calling pymad'
        #tic=time.time()
        #(x2,fs2,ignore)=audioread(fn,decoder='pymad',fs_target=fs_target,mono=False)
        #time2=time.time()-tic


        print 'Calling madplay'
        tic=time.time()
        (x3,fs3,ignore)=audioread(fn,decoder='madplay',fs_target=fs_target,mono=False)
        time3=time.time()-tic

        
        print 'mpg123  executetime=%2.2f secs=%s shape = %i %i, fs=%i' % (time1,get_secstr(len(x1)/fs1),shape(x1)[0],shape(x1)[1],fs1)
        #print 'pymad   executetime=%2.2f secs=%s shape = %i %i, fs=%i' % (time2,get_secstr(len(x2)/fs2),shape(x2)[0],shape(x2)[1],fs2)
        print 'madplay executetime=%2.2f secs=%s shape = %i %i, fs=%i' % (time3,get_secstr(len(x3)/fs3),shape(x3)[0],shape(x3)[1],fs3)
        print 'eyed3 secs=%s' % get_secstr(eyed3_secs)
        P.subplot(211)
        P.plot(x1[0:fs1*5,0],'r')
        #P.plot(x2[0:fs2*5,0],'g')
        P.plot(x3[0:fs3*5,0],'b')
        #P.legend(('mpg123','pymad','madplay'))
        P.legend(('mpg123','madplay'))
        P.subplot(212)
        P.plot(x1[0:fs1*5,1],'r')
        #P.plot(x2[0:fs2*5,1],'g')
        P.plot(x3[0:fs3*5,1],'b')
        P.xlabel('samples')
        P.title(fn)
        P.show()
    else :
        (x,fs,ignore)=audioread(fn,decoder=decoder,fs_target=fs_target,mono=mono)
        
        if len(shape(x))>1 and shape(x)[1]==2 :
            P.subplot(211)
            P.plot(N.arange(len(x))/float(fs),x[:,0])
            P.title(fn)
            P.xlabel('seconds')
            P.subplot(212)
            P.plot(N.arange(len(x))/float(fs),x[:,1])
            P.xlabel('seconds')
            P.show()
        else :
            P.plot(N.arange(len(x))/float(fs),x)
            P.xlabel('seconds')
            P.title(fn)
            P.show()





