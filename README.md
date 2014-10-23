# glftv-video-processor #

Python video-processing cli-prototype for converting mpeg-2 and mp4 (h.264) into the web-video-formats used by [GLFtv.de](http://glftv.de/).


===================
### Dependendencies
The following dependencies are needed

* Python 3.4+
* Python-rq
* Redis
* FFmpeg

=============
### CLI usage
Execute

```Shell
$ python cli/main.py
```

and follow the commandline prompt
```Shell
Input-Video-Path> ~/glftv-video-processor/test/test.mpg

2-pass Encoding (y/n)> y

Available profiles: webm mp4 ogv
Output-Video-Profile> all
```


============
### Todo

* Save profiles in a database
* Folder-worker
* Improve project-architecture
