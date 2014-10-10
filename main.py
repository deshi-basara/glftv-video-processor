__author__ = 'simon'

import os.path
import rq
from redis import Redis
from jobs import profile_job


class Profiles(object):

    #webm: ffmpeg -i *.mp4 -acodec libvorbis -ac 2 -ab 360k -ar 44100 -b:v 2000k -bufsize 2000k -threads 4 -pass 1 test2.webm
    #ogv:  ffmpeg -i *.mp4 -acodec libvorbis -ac 2 -ab 360k -ar 44100 -b:v 2000k -bufsize 2000k -threads 4 -pass 1 output.ogv
    #mp4:  ffmpeg -i *.mpg -acodec libfaac -ac 2 -ab 360k -ar 44100 -b:v 2000k -bufsize 2000k -threads 4 -pass 1 output.mp4
    profiles = {
        'webm': {'acodec':'libvorbis', 'ac': 2, 'ab': '360k', 'ar': 44100, 'b:v': '2000k', 'threads': 4},
        'ogv' : {'acodec':'libvorbis', 'ac': 2, 'ab': '360k', 'ar': 44100, 'b:v': '2000k', 'threads': 4},
        'mp4' : {'acodec':'libfaac', 'ac': 2, 'ab': '360k', 'ar': 44100, 'b:v': '2000k', 'threads': 4}
    }


class Model(object):

    def __init__(self, path, input_video, output_video, video_profile):
        self.path = path
        self.input = input_video
        self.output = output_video
        self.profile = video_profile

    def build_cmd(self):
        # get the settings of the selected profile
        selected_profile = Profiles.profiles[self.profile]
        # build the ffmpeg commandline string
        cmd = ['ffmpeg' , "-i", "%s/%s" % (self.path, self.input), "-y"]
        # add all settings
        for key, value in selected_profile.items():
            cmd.append("-%s" % key)
            cmd.append("%s" % value)
        # add the output
        cmd.append("%s/%s.%s" % (self.path, self.output, self.profile))
        return cmd


class View(object):

    def __init__(self):
        pass

    def available_profiles(self, profiles):
        # print all available profiles
        profile_output = 'Available profiles: '
        for profile in profiles:
            profile_output += profile + ' '
        print(profile_output)

    def error_path(self, input_video):
        print('PATH ERROR: ')
        print('The handed path "%s" does not exist' % input_video)
        print()

    def error_profile(self, input_profile):
        print('PROFILE ERROR: ')
        print('Specified profile "%s" does not exist' % input_profile)
        print()



class Controller(object):

    def __init__(self):
        # create needed objects
        self.profiles = Profiles()
        self.view = View()
        # initiate the queue
        self.queue = Queue()

    def set_input(self):
        # get the video path until the pass exists
        choosing = True
        while choosing:
            input_path = input("Input-Video-Path> ")
            # check if the path does exist
            if os.path.isfile(input_path) is not True:
                self.view.error_path(input_path)
            else:
                # get the absolute folder path and input filename
                self.path = os.path.dirname(input_path)
                self.input_video = os.path.basename(input_path)
                print(self.input_video)
                choosing = False

    def set_output(self):
        # split the file-extension from the path
        file_path, file_extenstion = os.path.splitext(self.input_video)
        # get the filename of our output file
        self.output_video = os.path.basename(file_path)
 
    def set_output_profile(self):
        # print all available profiles
        self.view.available_profiles(self.profiles.profiles)

        # let the user chose a profile
        choosing = True;
        while choosing:
            self.video_profile = input("Output-Video-Profile> ")
            # did the user enter a correct profile?
            if self.video_profile != 'all' and self.video_profile not in self.profiles.profiles.keys():
                self.view.error_profile(self.video_profile)
            else:
                choosing = False
      
    def start_conversion(self):
        # if the video file shall only be converted into a specific file
        if(self.video_profile != 'all'):
            # create a new video model and build the ffmpg-cmd
            self.model = Model(self.path, self.input_video, self.output_video, self.video_profile)
            cmd = self.model.build_cmd()
            # add the cmd to the queue
            self.queue.add(profile_job, cmd)
        # the user selected all, convert into all available profiles
        else: 
            # foreach profile, create a new model and add a job to the queue
            for profile in self.profiles.profiles:
                profile_model = Model(self.path, self.input_video, self.output_video, profile)
                profile_cmd = profile_model.build_cmd()
                # add the current profile to the queue
                self.queue.add(profile_job, profile_cmd)
        # start the worker
        self.queue.run()



class Queue(object):

    def __init__(self):
        # connect to redis
        redis_conn = Redis()
        self.q = rq.Queue(connection=redis_conn)

    def add(self, task, params):
        self.q.enqueue(task, params)

    def run(self):
        with rq.Connection():
            # start the task worker
            self.worker = rq.Worker(self.q)
            self.worker.work()
            print('Worker was startetd')



if __name__ == '__main__':

        # initiate the controller
        controller = Controller()

        # set the path of the video we want to convert
        controller.set_input()
        controller.set_output()

        # set the output profile
        controller.set_output_profile()

        # start conversion
        controller.start_conversion()