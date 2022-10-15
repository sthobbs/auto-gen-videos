
import moviepy.editor as mpy
import random
from pathlib import Path
from PIL import Image, ImageFont, ImageDraw 
import os
import hashlib
from tqdm import tqdm



class Video():

    def __init__(self, image_paths, output_dir, audio_dir, resolution='4K', fps=60, dur=6, delay=1, location=None, seed=None):
        self.image_paths = image_paths
        self.output_dir = output_dir # video output directory
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        self.dur = dur # clip duration (seconds)
        self.last_clip_dur = 16
        self.delay = delay # delay before text comes in on each clip
        self.location = Path(image_paths[0]).parent.parent.name if location == None else location
        self.fps = fps
        self.possible_animations = ['zoom-in', 'zoom-out', 'pan-right', 'pan-left']
        # set video resolution
        self.resolution = resolution
        self.w, self.h = self.get_resolution(resolution)
        print(f"resolution - {resolution}: {self.w} x {self.h}")
        # set seed based on location for reproducibility
        if seed is None:
            seed = int(hashlib.sha512(self.location.encode('cp1252')).hexdigest(), 16) % (10**6)
        random.seed(seed)
        self.audio_dir = audio_dir
        self.thumbnails_dir = 'thumbnails'

    def get_resolution(self, resolution=None):
        """set ouput video resolution"""
        if resolution is None:
            resolution = self.resolution
        possible_res = ['min', 'max', 'HD', 'FHD', 'QHD', '4K']
        assert resolution in possible_res or (type(resolution) == tuple and len(resolution) == 2), "invalid resolution"
        if resolution == 'min':
            w_ = min([mpy.ImageClip(p).w for p in image_paths]) # minimum width
            h_ = min([mpy.ImageClip(p).h for p in image_paths]) # minimum Height
            w = min(w_, int(h_ * 16 / 9)) # shrink to 16:9 ratio, images will conform to this width
            h = min(h_, int(w_ * 9 / 16)) # shrink to 16:9 ratio, images will conform to this height
        elif resolution == 'max':
            w_ = max([mpy.ImageClip(p).w for p in image_paths]) # maximum width
            h_ = max([mpy.ImageClip(p).h for p in image_paths]) # maximum Height
            w = max(w_, int(h_ * 16 / 9)) # expand to 16:9 ratio, images will conform to this width
            h = max(h_, int(w_ * 9 / 16)) # expand to 16:9 ratio, images will conform to this height
        elif type(resolution) == tuple and len(resolution) == 2:
            w, h = resolution
        elif resolution == 'HD':
            w, h = 1366, 768
        elif resolution == 'FHD':
            w, h = 1920, 1080
        elif resolution == 'QHD':
            w, h = 2560, 1440
        elif resolution == '4K':
            w, h = 3840, 2160
        return w, h
        
    def get_audio(self):
        """
        Gets path of random audio file from the self.audio_dir directory.
        """
        audio_paths = [f"{self.audio_dir}\\{file}" for file in os.listdir(f"{self.audio_dir}")]
        path = random.choice(audio_paths)
        return path 
    
    def slide_left(self, t, h, w, h_pos=0.03, v_pos=0.87, h_speed=1.0, v_speed=0.5, v_time=5, relative=True):
        """
        A function of time t -> (x,y) coordinates, that specifies the movement path for animated text
        as it slides in from the right side of the screen, pauses, then slides down off the screen.
        
        Parameters
        -----------

        t
            Time, in seconds, from the start of the clip.

        h
            Height of the image/video in pixels that the text with overlay.
            Not used if relative=False

        w
            Height of the image/video in pixels that the text with overlay.

        h_pos
            Horizonatal position that the text stops.

        v_pos
            Vertial position that the text maintains before moving down.

        h_speed
            Speed at which the text moves left (number of screens per second).

        v_speed
            Speed at which text moves down (number of screens per second).

        v_time
            Time until text starts moving down, in seconds, from the start of the TextClip.

        relative
            ``True`` (default) if you want h_pos, v_pos, h_speed, and v_speed to be relative
            to the size of the image/video that the text is on top of (i.e. relative to h and w),
            rather than based on number of pixels.


        Formula derivation
        -----------
        Horizontal
            Need y = a*t + b, such that (t,y) = (0, w) is a solution so that the text starts off the right side of the screen, and
            a = -h_speed, so
            b = w, and
            y = -h_speed * t + w

        Vertical
            Need y = a*t + b, such that (t,y) = (v_time, v_pos) as a solution so that it starts moving down at v_time, and
            a = v_speed, so
            b = v_pos - v_speed * v_time, and
            y = v_speed * t + v_pos - v_speed * v_time
              = v_speed * (t - v_time) + v_pos
        """
        w, h = self.w, self.h

        if relative:
            assert h is not None and w is not None, 'Must provide non-None values of h and w if relative=True'
            # scale positions and speeds so that they're relative to the size of the image/video the text is composed with
            h_pos *= w
            v_pos *= h
            h_speed *= w
            v_speed *= h

        x = max(h_pos, -h_speed * t + w)
        y = max(v_pos, v_speed * (t - v_time) + v_pos)
        return (x, y)

    def crop_to_aspect(self, image_clip, aspect_ratio=16/9, allow_slight_stretching=False, max_stretch=1.2):
        """
        Stretch and/or crop ImageClip to specified aspect ratio.

        Parameters
        -----------

        image_clip
            An ImageClip object.

        aspect_ratio
            The desired aspect ratio of the returned ImageClip.

        allow_slight_stretching
            If ``True``, then stretch towards the desired aspect ratio (up to max_stretch),
            before cropping if the desired aspect ratio is still not achieved.

        max_stretch
            The max rate the image can be stretched (e.g. 1.2 means one dimension can be
            stretched by at most a factor of 1.2)
        """
        w, h = image_clip.w, image_clip.h
        # if allowed, first stretch the image to be closer to the desired aspect ratio
        if allow_slight_stretching:
            if w / h > aspect_ratio * max_stretch: # very wide image
                new_h = h * max_stretch
                new_w = w
            elif w / h < aspect_ratio / max_stretch: # very tall image
                new_h = h
                new_w = w * max_stretch
            elif w / h >= aspect_ratio: # slightly wide image
                new_h = w / aspect_ratio
                new_w = w
            elif w / h < aspect_ratio: # slightly tall image
                new_h = h
                new_w = h * aspect_ratio
            image_clip = image_clip.resize((new_w,new_h))
            w, h = new_w, new_h
        # crop image 
        new_w = min(w, int(h * aspect_ratio))
        new_h = min(h, int(w / aspect_ratio))
        x1 = (w - new_w) / 2
        x2 = w - x1
        y1 = (h - new_h) / 2
        y2 = h - y1
        image_clip = image_clip.crop(x1=x1, x2=x2, y1=y1, y2=y2)
        return image_clip

    def pick_animation(self, w, h):
        """
        Picks appropriate animation based on aspect ratio. Images wider than 16 x 9 get a
        horizontal pan animation, otherwise a zoom animation is picked.

        Parameters
        -----------

        w
            width of the image. Aspect ratio is used to pick the type of animation.

        h
            height of the image. Aspect ratio is used to pick the type of animation.
        """
        if w / h > 16 / 9: # wide image
            animation = random.choice(['pan-right', 'pan-left'])
        else:
            animation = random.choice(['zoom-in', 'zoom-out'])
        return animation

    def add_animation(self, image_clip, animation='random', scroll_dist=0.2):
        """
        Applies one of the following animations to an ImageClip:
            1. Zoom in
            2. Zoom out
            3. Pan right
            4. Pan left

        Parameters
        -----------

        image_clip
            An ImageClip object.

        animation
            A string representing the animation to apply ('zoom-in', 'zoom-out', 'pan-right', 'pan-left') or 'random'

        scroll_dist
            The scroll/pan distance (relative to the image width) for scroll/panning animations
        """
        w, h, dur = self.w, self.h, self.dur
        s = scroll_dist

        if animation == 'random':
            animation = random.choice(self.possible_animations)
        assert animation in self.possible_animations, f"animation must be in {self.possible_animations}, not {animation}"

        # resize image to prep for animation
        if animation[:3] == 'pan': # prep for horizontal pan effect on wide images
            # crop image to modified aspect ratio
            aspect_correction =  1 / (1 - s) # correct aspect ratio for scroll/pan transformation
            image_clip = self.crop_to_aspect(image_clip, aspect_ratio=aspect_correction*16/9, allow_slight_stretching=True)
            # scale image to same number of pixels as other images (plus correction factor) 
            image_clip = image_clip.resize((aspect_correction*w,h))
        else: # prep for zoom effect on tall images
            # crop image to 16:9 aspect ratio
            image_clip = self.crop_to_aspect(image_clip, aspect_ratio=16/9, allow_slight_stretching=True)
            # scale image to same number of pixels as other images (which is usually to 16:9 aspect ratio) 
            image_clip = image_clip.resize((w,h))

        # animate image
        if animation == 'zoom-in':
            image_clip = image_clip.resize(lambda t : 1+0.02*t)
        elif animation == 'zoom-out':
            # The .resize() method scales relative to the t=0 output, so I added the t=0 case.
            image_clip = image_clip.resize(lambda t: 1 if t==0 else 1+0.02*(dur-t))
        elif animation == 'pan-right':
            # scroll() squishes the image horizontally, we previously cropped to an extra wide aspect ratio to offset this.
            # resize() is applied so the output can be correctly combined with the TextClip later.
            image_clip = mpy.vfx.scroll(image_clip, w=int((1-s)*w), x_speed=s*w/dur)
            image_clip = image_clip.resize((w,h))
        elif animation == 'pan-left':
            # scroll only pans right, so image_clip is flipped before and after the scroll operation to get a left pan
            image_clip = mpy.vfx.mirror_x(image_clip)
            image_clip = mpy.vfx.scroll(image_clip, w=int((1-s)*w), x_speed=s*w/dur, x_start=0)
            image_clip = mpy.vfx.mirror_x(image_clip)
            image_clip = image_clip.resize((w,h))
        
        return image_clip

    def process_image(self, image_path, last_clip=False):
        """
        Generate an edited ImageClip based on an image file.

        Parameters
        -----------

        image_path
            path to an image file to be used to generate the ImageClip.

        last_clip
            if ``True``, use custom edits intended for the last clip in the video. Specifically,
            use a longer clip duration and include an animated subscribe button.
        """

        # use custom edits for the last clip
        if last_clip:
            dur = self.last_clip_dur # longer duration
            animation = 'zoom-in' # zoom-in animation
            # make masked subscribe animation overlay
            subscribe_path = 'subscribe.mp4'
            sub_clip = mpy.VideoFileClip(subscribe_path).set_duration(5).set_start(7)
            sub_clip = sub_clip.fx(mpy.vfx.mask_color, color=[15, 209, 0], thr=125, s=30) # RGB of green screen determined in MS paint
            # crop off border
            w, h = sub_clip.w, sub_clip.h
            new_w, new_h = int(0.9 * w), int(0.9 * h)
            x1 = int((w - new_w) / 2)
            x2 = w - x1
            y1 = int((h - new_h) / 2)
            y2 = h - y1
            sub_clip = sub_clip.crop(x1=x1, y1=y1, x2=x2, y2=y2)
            # resize
            sub_clip = sub_clip.resize((self.w, self.h)) # resize to same as youtube video
            sub_clip = sub_clip.resize(0.25).set_pos(('right', 'bottom')) # shrink and put in bottom right corner
            # add short fade in and out
            sub_clip = sub_clip.crossfadein(0.25).crossfadeout(0.25)
        else:
            dur = self.dur
            animation = 'random'
        # Make clip from image
        image_clip = mpy.ImageClip(image_path, duration=dur)
        # pick random animation (picking it before the crop since I want to crop less initally if I'm panning)
        if animation == 'random':
            animation = self.pick_animation(image_clip.w, image_clip.h)
        # Animate image -- either zoom in, zoom out, pan right, or pan left
        image_clip = self.add_animation(image_clip, animation=animation)
        # Add crossfade transitions
        image_clip = image_clip.crossfadein(1).crossfadeout(1)
        # add subscribe animation if it's the last clip
        if last_clip:
            image_clip = mpy.CompositeVideoClip([image_clip, sub_clip])
        return image_clip

    def process_text(self, text):
        w, h, dur, delay = self.w, self.h, self.dur, self.delay
        # Make clip from text
        text_clip = mpy.TextClip(txt=text, fontsize=0.067*h, font='Amiri-regular', color='white')
        # Add box around text
        text_clip = text_clip.on_color(size=(w, int(1.2*text_clip.h)), color=(0,0,0), pos=(0.025*w, 'center'), col_opacity=0.6)
        # Animate text clip
        text_clip = text_clip.set_duration(dur-delay).set_start(delay)
        text_clip = text_clip.set_position(lambda t: self.slide_left(t, h, w, h_pos=0.03, v_pos=0.81, h_speed=2.0, v_speed=0.5, v_time=dur-3))
        return text_clip

    def gen_clip(self, image_path, text, last_clip=False):
        """
        Make an animated clip out of an image and text.
        """
        # Make & process ImageClip
        image_clip = self.process_image(image_path, last_clip)
        # Make & process TextClip
        text_clip = self.process_text(text)
        # Overlay the TextClip onto ImageClip
        clip = mpy.CompositeVideoClip([image_clip, text_clip])
        return clip

    def gen_video(self):
        # generate clips
        clips = []
        for i in range(len(self.image_paths)):
            path = self.image_paths[i]
            attraction = '.'.join(Path(path).name.split('.')[:-1])
            clip_text = f"{i+1}. {attraction}"
            last_clip = (i == 0) # last clip (after the order is reversed)
            clip = self.gen_clip(path, clip_text, last_clip)
            clips.append(clip)
        clips.reverse()
        # combine clips and audio
        video = mpy.concatenate_videoclips(clips, method='compose', padding=-1)
        audio_path = self.get_audio() # get random song
        video_length = (self.dur - 1) * (len(clips) - 1) + (self.last_clip_dur - 1) # video length (seconds)
        audio = mpy.AudioFileClip(audio_path).set_duration(video_length).audio_fadein(1).audio_fadeout(2)
        combined_audio = mpy.CompositeAudioClip([video.audio, audio])
        video = video.set_audio(combined_audio)
        # render video
        output_path = f"{self.output_dir}\\{self.location}.mp4"
        video.write_videofile(output_path, fps=self.fps, threads=6, codec='mpeg4')

    def gen_thumbnail(self, input_path=None, output_path=None, title=None, resolution=None):
        # get path to image
        if input_path is None:
            input_path = random.choice(self.image_paths)
        # open image
        img = Image.open(input_path)
        # crop to 16:9 aspect ratio
        w, h = img.size
        new_w = min(w, int(h * 16 / 9))
        new_h = min(h, int(w * 9 / 16))
        x1 = int((w - new_w) / 2)
        x2 = w - x1
        y1 = int((h - new_h) / 2)
        y2 = h - y1
        img = img.crop((x1,y1,x2,y2))
        # set sizes (for clearer text)
        if resolution is None:
            resolution = self.resolution
        new_w, new_h = self.get_resolution(resolution)
        img = img.resize((new_w, new_h))
        # make image editable
        draw = ImageDraw.Draw(img)
        # set up font
        font_size = int(0.25 * new_h)
        stroke_width = max(2, int(font_size / 100))
        font_type = 'arialbd.ttf'
        font = ImageFont.truetype(font_type, font_size) 
        # add text to image
        # line 1 (e.g. "TOP 10")
        txt = f"TOP {len(self.image_paths)}"
        w, h = draw.textsize(txt, font=font) # size of text
        x = int((new_w - w) / 2)
        y = int(0.45 * new_h - h)
        draw.text((x, y), txt, (237, 230, 211), font=font, stroke_width=stroke_width, stroke_fill="black") # Centered horizontally, just above midpoint vertically
        # add line 2 (e.g. "TORONTO")
        txt = f"{self.location.split(',')[0].upper()}" if title is None else title 
        w, h = draw.textsize(txt, font=font)
        while w > 0.975 * new_w: # reduce font if it doesn't fit on the picture
            font_size -= 1
            font = ImageFont.truetype(font_type, font_size) 
            w, h = draw.textsize(txt, font=font)
        #stroke_width = max(1, int(font_size / 100)) # reset stroke size for possibly new font size
        x = int((new_w - w) / 2)
        y = int(0.52 * new_h)
        draw.text((x,y), txt, (237, 230, 211), font=font, stroke_width=stroke_width, stroke_fill="black") # Centered horizontally, just below midpoint vertically
        # save image
        if output_path is None:
            attraction = '.'.join(Path(input_path).name.split('.')[:-1])
            output_path = f"{self.output_dir}\\{self.thumbnails_dir}\\{attraction}.png"
        img.save(output_path, "PNG")
        #print(f"saved thumbnail to {output_path}")

    def gen_thumbnails(self, title=None, resolution=None, sub_dir=None):
        output_dir = f"{self.output_dir}\\{self.thumbnails_dir}"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        if sub_dir is not None:
            output_dir = f"{self.output_dir}\\{self.thumbnails_dir}\\{sub_dir}"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
        if resolution is None:
            resolution = self.resolution
        print(f"generating {resolution} thumbnails for {self.location}")
        for i in tqdm(range(len(self.image_paths))):
            input_path = self.image_paths[i]
            attraction = '.'.join(Path(input_path).name.split('.')[:-1])
            output_path = f"{output_dir}\\{attraction}.png"
            self.gen_thumbnail(input_path=input_path, output_path=output_path, title=title, resolution=resolution)

    def document(self):
        """
        generates a txt file that with the video title and description
        """
        output_path = f"{self.output_dir}\\description.txt"
        title = f"Top {len(self.image_paths)} Things to do in {self.location.split(',')[0].upper()}"
        description = f"In this video, we'll show you the top {len(self.image_paths)} things that you have to do when you're in {self.location}!\n\n\n\nMusic from www.bensound.com"
        text = f"Title:\n{title}\n\nDescription:\n{description}"
        # write text to file
        with open(output_path, 'w') as file:
            file.write(text)
        print(f"saved description to {output_path}")





# possible next steps;
    # add in any new things
        # maybe an intro
    # get more music
    # connect directly to youtube API
    # review moviepy docs for ideas
    # clean up bing scraping code

