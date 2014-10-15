__author__ = 'simon'

import os.path
import rq
from redis import Redis
from jobs import profile_job


class Profiles(object):

    """All available convertion profiles and their commandline parameters.

    webm: ffmpeg -i *.mp4 -acodec libvorbis -ac 2 -ab 360k -ar /
            44100 -b:v 2000k -bufsize 2000k -threads 4 -pass 1 test2.webm
    ogv:  ffmpeg -i *.mp4 -acodec libvorbis -ac 2 -ab 360k -ar /
            44100 -b:v 2000k -bufsize 2000k -threads 4 -pass 1 output.ogv
    mp4:  ffmpeg -i *.mpg -acodec libfaac -ac 2 -ab 360k -ar /
            44100 -b:v 2000k -bufsize 2000k -threads 4 -pass 1 output.mp4
    """
    profiles = {
        'webm': {
            # audio
            'codec:a': 'libvorbis',
            'ac': 2,
            'ar': 44100,
            'b:a': '360k',
            # video
            'codec:v': 'libvpx',
            'quality': 'good',
            'cpu-used': 0,
            'b:v': '2000k',
            'qmin': 10,
            'qmax': 42,
            'maxrate': '2000k',
            'bufsize': '4000k',
            'vf': 'scale=-1:720',
            'threads': 4
        },
        'ogv': {
            'acodec': 'libvorbis',
            'ac': 2,
            'ab': '360k',
            'ar': 44100,
            'b:v': '2000k',
            'bufsize':
            '2000k',
            'threads': 4
        },
        'mp4': {
            'acodec': 'libfaac',
            'ac': 2,
            'ab': '360k',
            'ar': 44100,
            'b:v': '2000k',
            'bufsize': '2000k',
            'threads': 4
        }
    }


class Model(object):

    """Model representation of a video"""

    def __init__(self, path, input_video, output_video, video_profile, two_pass):
        """
        Set all needed Model attributes.

        :arg path:          absolute baseBath of the video
        :arg input_video:   name of the input video
        :arg output_video:  name of the output video
        :arg video_profile: selected profile from Profile.profiles
        :arg two_pass:      two-pass setting as bool
        """
        self.path = path
        self.input = input_video
        self.output = output_video
        self.profile = video_profile
        self.two_pass = two_pass

    def build_cmd(self):
        """ Build the ffmpeg-commandline command """
        # get the settings of the selected profile
        selected_profile = Profiles.profiles[self.profile]
        # build the ffmpeg commandline string
        cmd = ['ffmpeg', "-i", "%s/%s" % (self.path, self.input), "-y"]
        # add all settings from the profile
        for key, value in selected_profile.items():
            cmd.append("-%s" % key)
            cmd.append("%s" % value)
        # make a two pass cmd if it was set
        if self.two_pass is True:
            # dublicate the cmd, add pass 1 & output file
            cmd_pass_one = list(cmd)
            cmd_pass_one.extend(["-pass", "1", "%s/%s.%s" % (self.path, self.output, self.profile)])
            # dublicate the cmd, add pass 2 & output file
            cmd_pass_two = list(cmd)
            cmd_pass_two.extend(["-pass", "2", "%s/%s.%s" % (self.path, self.output, self.profile)])
            # concat them to a valid linux command
            return [cmd_pass_one, cmd_pass_two]
        else:
            # add the output
            cmd.append("%s/%s.%s" % (self.path, self.output, self.profile))
            return [cmd]


class View(object):

    """ CLI-View and their output functions """

    def __init__(self):
        pass

    def available_profiles(self, profiles):
        """ Print all available profiles """
        profile_output = 'Available profiles: '
        for profile in profiles:
            profile_output += profile + ' '
        print(profile_output)

    def error_path(self, input_video):
        """ Print an error, when the user selected a wrong path """
        print('PATH ERROR: ')
        print('The handed path "%s" does not exist' % input_video)
        print()

    def error_profile(self, input_profile):
        """ Print an error, when the user selected a wrong profile """
        print('PROFILE ERROR: ')
        print('Specified profile "%s" does not exist' % input_profile)
        print()

    def error_yes_no():
        """ Print an error, when the user input is not a valid y/n """
        print("Invalid input, try it again")


class Controller(object):

    """ CLI-Controller """

    def __init__(self):
        """ Create needed objects """
        self.profiles = Profiles()
        self.view = View()
        self.queue = Queue()

    def set_input(self):
        """ Get the video path until the pass exists """
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
                choosing = False

    def set_output(self):
        """ Set the videos output_path and output_name """
        # split the file-extension from the path
        file_path, file_extenstion = os.path.splitext(self.input_video)
        # get the filename of our output file
        self.output_video = os.path.basename(file_path)

    def set_pass(self):
        """Ask the user if he wants a 2-pass convertion"""
        choosing = True
        while choosing:
            input_pass = input("2-pass Conversion (y/n)> ")
            # check if the user entered a valid input
            if input_pass == "y":
                self.two_pass = True
                choosing = False
                continue
            elif input_pass == "n":
                self.two_pass = False
                choosing = False
                continue
            # if the input wasn't correct
            self.model.error_yes_no()

    def set_output_profile(self):
        """ Set the output profile """
        # print all available profiles
        self.view.available_profiles(self.profiles.profiles)

        # let the user chose a profile
        choosing = True
        while choosing:
            self.video_profile = input("Output-Video-Profile> ")
            # did the user enter a correct profile?
            if self.video_profile != 'all' and self.video_profile not in self.profiles.profiles.keys():
                    self.view.error_profile(self.video_profile)
            else:
                choosing = False

    def start_conversion(self):
        """ Start the video conversion process """
        # if the video file shall only be converted into a specific file
        if(self.video_profile != 'all'):
            # create a new video model and build the ffmpg-cmd
            self.model = Model(self.path, self.input_video, self.output_video, self.video_profile, self.two_pass)
            cmd = self.model.build_cmd()
            # add each cmd to the queue
            for ffmpeg_cmd in cmd:
                print(ffmpeg_cmd)
                self.queue.add(profile_job, ffmpeg_cmd)
        # the user selected all, convert into all available profiles
        else:
            # foreach profile, create a new model and add a job to the queue
            for profile in self.profiles.profiles:
                profile_model = Model(
                    self.path, self.input_video, self.output_video, profile)
                profile_cmd = profile_model.build_cmd()
                # add each cmd to the queue
                for ffmpeg_cmd in profile_cmd:
                    self.queue.add(profile_job, ffmpeg_cmd)
        # start the worker
        self.queue.run()


class Queue(object):

    def __init__(self):
        """ Let the python-rq-Queue connect to redis """
        redis_conn = Redis()
        self.q = rq.Queue(connection=redis_conn)

    def add(self, task, params):
        """ Add a new commandline job """
        self.q.enqueue(task, params, timeout=None)

    def run(self):
        """ Run the queue-worker """
        with rq.Connection():
            # start the task worker
            self.worker = rq.Worker(self.q)
            self.worker.work()
            print('Worker was startetd')


if __name__ == '__main__':

    # initiate the controller
    controller = Controller()

    # set the path of the video we want to convert and 2-pass
    controller.set_input()
    controller.set_output()
    controller.set_pass()

    # set the output profile
    controller.set_output_profile()

    # start conversion
    controller.start_conversion()