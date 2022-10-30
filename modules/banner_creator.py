#Banner Creator
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageColor
import pathlib
import random

import AMP
import DB
import logging

class fake_server():
    def __init__(self):
        self.DisplayName = 'All The Mods 7: To The Sky'
        self.Description = 'All the Mods 7 To the Sky is the sequel to the popular atm6 sky, we have taken feedback from the first iteration to make this pack the best we have to offer, adding in mods that were not in the first, such as Twilight Forest and Alchemistry, followed by the mod ex machinis, an automation addon for ex nihilo built in house by ATM to take you from early, all the way to end game automated resources.'
        self.IP = '192.168.3.50:25565'
        self.Whitelist = 1#random.randint(0,1)
        self.Donator = 1#random.randint(0,1)
        self.Status = 1#random.randint(0,1)
        self.Player_Limit = random.randint(0,20)
        self.Players_Online = ['k8_thekat', 'Lightning', 'Alain', 'Dann', 'Saorie', 'IceofWraith', 'BigO','Steve','k8_thekat', 'Lightning', 'Alain', 'Dann', 'Saorie', 'IceofWraith', 'BigO','Steve']
        self.Nicknames = ['ATM7 Sky', 'ATM7SKY','ATM7 to the Sky', 'All the Mods 7: Sky', 'ATM7:Sky', 'All The Mods 7: To the Sky']

class Banner_Generator():
    """Custom Banner Generator for Gatekeeper. """
    def __init__(self, AMPServer:AMP.AMPInstance, DBBanner:DB.DBBanner, Banner_path:str=None, blur_background:bool=None):
        self._font = pathlib.Path("resources/fonts/ReemKufiFun-Regular.ttf").as_posix()
        self._logger = logging.getLogger()
        #Turn that str into a Purepath for cross OS support
        self._font_default_size = 25
        self._font_default = ImageFont.truetype(self._font, self._font_default_size)
        self._font_drop_shadow_size = (int(self._font_default_size / 5), int(self._font_default_size / 5))

        if Banner_path == None:
            Banner_path = AMPServer.background_banner_path
            if Banner_path == None:
                Banner_path = AMPServer.default_background_banner_path

        self._banner_limit_size_x = 1800
        self._banner_limit_size_y = 600
        self.banner_image = self._validate_image(pathlib.Path(Banner_path).as_posix())

        self._Server = AMPServer
        
        if DBBanner.blur_background_amount != 0:
            self._blur_background(blur_power= DBBanner.blur_background_amount)

        self._banner_shadow_box = (int(self._banner_limit_size_x / 3.5),self._banner_limit_size_y) #x,y)
        self._banner_shadow_box_x = int(self._banner_limit_size_x - self._banner_shadow_box[0])

        self._center_align_Body = int(((self._banner_limit_size_x - self._banner_shadow_box[0]) /2))

        self._font_Header_size = int(self._font_default_size * 5)
        self._font_Header_color =  DBBanner.color_header #Really light Blue
        #self._font_Header_color =  "#85c1e9" #Really light Blue
        self._font_Header = ImageFont.truetype(self._font, self._font_Header_size)
        self._font_Header_text_height = self._font_Header.getbbox('W')[-1]

        self._font_Nickname_size = int(self._font_default_size * 2.5)
        self._font_Nickname_color = DBBanner.color_nickname
        # self._font_Nickname_color = "#f2f3f4"
        self._font_Nickname = ImageFont.truetype(self._font, self._font_Nickname_size)
        self._font_Nickname_text_height = self._font_Nickname.getbbox('W')[-1]

        self._font_Body_size = int(self._font_default_size * 2)
        self._font_Body_line_offset = 0
        self._font_Body_color = DBBanner.color_body #Off White
        # self._font_Body_color = "#f2f3f4" #Off White
        self._font_Body = ImageFont.truetype(self._font, self._font_Body_size)
        self._font_Body_text_height = self._font_Body.getbbox('W')[-1]

        self._font_IP_color = DBBanner.color_IP
        # self._font_IP_color = "#5dade2"
        self._font_IP_size = int(self._font_default_size * 3)
        self._font_IP = ImageFont.truetype(self._font, self._font_IP_size)
        self._font_IP_text_height = self._font_IP.getbbox('W')[-1]

        self._font_Whitelist_Donator_size = int(self._font_default_size * 3.5)
        self._font_Whitelist_color_open =  DBBanner.color_whitelist_open
        self._font_Whitelist_color_closed = DBBanner.color_whitelist_closed
        # self._font_Whitelist_color_open =  "#f7dc6f"
        # self._font_Whitelist_color_closed = "#cb4335"
        # self._font_Donator_color = "#212f3c"
        self._font_Donator_color = DBBanner.color_donator
        self._font_Whitelist_Donator = ImageFont.truetype(self._font, self._font_Whitelist_Donator_size)
        self._font_Whitelist_Donator_text_height = self._font_Whitelist_Donator.getbbox('W')[-1]
        
        self._font_Status_size = int(self._font_default_size * 3)
        self._font_Status = ImageFont.truetype(self._font, self._font_Status_size)
        self._font_Status_text_height = self._font_Status.getbbox('W')[-1]

        self._font_Status_color_online = DBBanner.color_status_online
        # self._font_Status_color_online = "#28b463" #Green
        self._font_Status_text_length_Online = self._font_Status.getlength('Online: ')

        self._font_Status_color_offline =  DBBanner.color_status_offline
        # self._font_Status_color_offline =  "#e74c3c" #Red
        self._font_Status_text_length_Offline = self._font_Status.getlength('Offline')

        self._font_Player_Limit_size = int(self._font_default_size * 2)
        self._font_Player_Limit_color_max = DBBanner.color_player_limit_max
        self._font_Player_Limit_color_min = DBBanner.color_player_limit_min
        # self._font_Player_Limit_color_max = "#ba4a00"
        # self._font_Player_Limit_color_min = "#5dade2"
        self._font_Player_Limit = ImageFont.truetype(self._font, self._font_Player_Limit_size)
        self._font_Player_Limit_text_height = self._font_Player_Limit.getbbox('W')[-1]

        self._font_Player_Online_size = int(self._font_default_size * 2) 
        self._font_Player_Online_color = DBBanner.color_player_online
        # self._font_Player_Online_color = "#f7dc6f" #white
        self._font_Player_Online = ImageFont.truetype(self._font, self._font_Player_Online_size)
        self._font_Player_Online_text_height = self._font_Player_Online.getbbox('W')[-1]
        
        self._shadow_box()
        self._Server_Name()
        self._Server_Status()
        self._Server_NickNames()
        self._Server_Whitelist_Donator()
        self._Server_Description()
        self._Server_Players_Online()
        self._Server_IP()
        #This MUST BE CALLED LAST
        self._round_corners()

    def _image_(self):
        return self.banner_image

    def _validate_image(self, path)-> Image.Image:
        try:
            image = Image.open(path)

            image = image.resize(size=(self._banner_limit_size_x, self._banner_limit_size_y), resample= Image.Resampling.BICUBIC)

            if image.mode != 'RGBA':
                image = image.convert(mode= 'RGBA')
            return image
        except:
            raise

    def _blur_background(self, blur_power:int=2):
        """Blurs the Background Image with GaussianBlur"""
        self.banner_image = self.banner_image.filter(ImageFilter.GaussianBlur(blur_power))
        return 

    def _word_wrap(self, text:str, text_font:ImageFont.ImageFont, text_size:int, limit:int, find_char:str, truncate:bool=True):
        """Custom Word Wrap. \n
        Returns a `list` when `truncate` is `False`"""
        #No need to word wrap if the length is less than our cutoff.
        if ImageFont.truetype(text_font, text_size).getlength(text) < limit:
            return text

        if text.find(find_char) == -1:
            return None

        split_test_str = text.split(find_char)
        temp_list = []
        temp_str = ''
        for i in range(0,len(split_test_str)):
            cur_str = temp_str
            temp_str += split_test_str[i] + find_char
            if ImageFont.truetype(text_font, text_size).getlength(temp_str) < limit:
                continue
            
            elif truncate == True:
                #Removes the extra char at the end when we truncate.
                return cur_str[:(len(cur_str)-1)]

            elif truncate == False:
                temp_list.append(cur_str)
                temp_str = ''

        return temp_list

    def _color_gradient(self):
        """Adjusted the RGB values for Player Limit Display."""
        min_rgb = ImageColor.getrgb(self._font_Player_Limit_color_min)
        max_rgb = ImageColor.getrgb(self._font_Player_Limit_color_max)
        final_rgb = [0,0,0]
        players_online = random.randint(0,8)
        if int(self.user_count[0]) == 0:
            return min_rgb

        for color in range(0,len(min_rgb)):
            temp_rgb = min_rgb[color] - max_rgb[color]
            temp_rgb/= int(self.user_count[0])
            temp_rgb*= players_online
            temp_rgb += min_rgb[color]
            final_rgb[color] = int(temp_rgb)
        return tuple(final_rgb)

    def _round_corners(self):
        """Rounds the corners of the Background Image."""
        image = Image.new('RGBA', [self._banner_limit_size_x, self._banner_limit_size_y])
        image_draw = ImageDraw.Draw(image)
        image_draw.rounded_rectangle([(0,0),(self._banner_limit_size_x, self._banner_limit_size_y)], radius=40, fill=(0,0,0))
        image.paste(self.banner_image, (0,0), mask= image)
        self.banner_image = image
 
    def _draw_text(self, xy:tuple, text:str, font:ImageFont.ImageFont, fill=None, drop_shadow_fill=None, drop_shadow_blur=1):
        if type(drop_shadow_fill) == str:
            drop_shadow_fill = ImageColor.getrgb(drop_shadow_fill)
        
        if drop_shadow_fill == None:
            drop_shadow_fill = (0,0,0)

        if type(fill) == str:
            fill = ImageColor.getrgb(fill)

        image_size = font.getbbox(text= text)
        shadow = Image.new('RGBA', [int(image_size[2] + self._font_drop_shadow_size[0]) , int(image_size[3] + self._font_drop_shadow_size[1])])
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.text(xy= self._font_drop_shadow_size, text= text, fill= drop_shadow_fill, font= font)
        shadow = shadow.filter(ImageFilter.GaussianBlur(drop_shadow_blur))

        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.text(xy=(0,0), text= text, fill= fill, font= font)

        self.banner_image.paste(shadow, xy, mask= shadow)

    def _shadow_box(self):
        """Draws the Shadowbox for Players and Status on the right side of the banner."""
        box = Image.new('RGBA', [self._banner_shadow_box[0]+10, self._banner_shadow_box[1]])
        box_draw = ImageDraw.Draw(box)
        box_draw.rounded_rectangle([(10,0), (self._banner_shadow_box[0]+10, self._banner_shadow_box[1])], radius= 40, fill= (0,0,0,175))
        box = box.filter(ImageFilter.GaussianBlur(2))
        self.banner_image.paste(box, (self._banner_shadow_box_x, 0), mask= box)

    def _Server_Name(self):
        """Displays the Server Name"""
        x,y = 25,0
        name = self._Server.FriendlyName
        if self._Server.DisplayName != None:
            name = self._Server.DisplayName

        self._draw_text((x,y), name, self._font_Header, self._font_Header_color)
    
    def _Server_NickNames(self):
        self._font_Nicknames_y = self._font_Header_text_height + 5
        if self._Server.Nicknames != None and len(self._Server.Nicknames) > 0:
            x,y = (50, self._font_Nicknames_y)
            text = "Nicknames: " + " , ".join(self._Server.Nicknames)
            text = self._word_wrap(text, self._font, self._font_Nickname_size, (self._banner_shadow_box_x - x), ',' , True )
            self._draw_text((x,y), text, self._font_Nickname, self._font_Nickname_color)

    def _Server_IP(self):
        self._font_IP_y = self._font_Nicknames_y + self._font_Body_text_height
        if self._Server.Display_IP not in [None, '', 'None']:
            text = 'Host: ' + self._Server.Display_IP
            #offset = int(ImageFont.truetype(self._font, self._font_IP_size).getlength(text)/2)
    
            x,y = (25, self._font_IP_y)
            self._draw_text((x,y), text, self._font_IP, self._font_IP_color)

    def _Server_Whitelist_Donator(self):
        self._font_Whitelist_Donator_y = int(self._font_Header_text_height + self._font_Nickname_text_height + self._font_IP_text_height + 15)
        text = 'Whitelist Closed'
        color = self._font_Whitelist_color_closed
        shadow_color = None

        if self._Server.Whitelist == 1 and self._Server.ADS_Running != 0:
            text = 'Whitelist Open'
            color = self._font_Whitelist_color_open

            if self._Server.Donator == 1:
                text += ' - [Donator Only]'
                color = self._font_Donator_color
                shadow_color = '#3498db'

        offset = ImageFont.truetype(self._font, self._font_Whitelist_Donator_size).getlength(text)
        x,y = (int(self._center_align_Body - (offset / 2)), self._font_Whitelist_Donator_y)
        self._draw_text((x,y), text= text, font= self._font_Whitelist_Donator, fill= color, drop_shadow_fill= shadow_color)

    def _Server_Description(self):
        x,y= (15, (self._banner_limit_size_y - (self._font_Body_text_height * 2) - 8))

        if self._Server.Description != None:
            text = self._word_wrap(self._Server.Description, self._font, self._font_Body_size, (self._banner_shadow_box_x - x), ' ', False)
            if type(text) == list:
                for entry in text:
                    self._draw_text((x,y), entry, self._font_Body, self._font_Body_color)
                    x = x
                    y += self._font_Body_text_height
  

    def _Server_Status(self):
        text = 'Offline'
        fill = self._font_Status_color_offline
        padding = int((self._banner_shadow_box[0] - self._font_Status_text_length_Offline) / 2)
        if self._Server.ADS_Running == 1:
            text = 'Online: '
            fill = self._font_Status_color_online
            #This will change depending on the player limit of the server.
            self.user_count = self._Server.getStatus(users_only= True)
            user_count_text = f'{self.user_count[0]} / {self.user_count[1]}'
            text_length = ImageFont.truetype(self._font, self._font_Status_size).getlength(text + user_count_text)
            padding = int((self._banner_shadow_box[0] - text_length) / 2)

            y = 0
            x = int(self._banner_shadow_box_x + padding + self._font_Status_text_length_Online)
            self._draw_text((x,y),user_count_text, self._font_Status, self._color_gradient())

        x,y = ((self._banner_shadow_box_x + padding), 0)
        self._draw_text((x,y), text, self._font_Status, fill)

    def _Server_Players_Online(self):
        index = 0
        if self._Server.ADS_Running != 0:
            y = self._font_Status_text_height
            for entry in self._Server.getUserList():
                if index > 8:
                    return
                index += 1
                center_align = int((self._banner_shadow_box[0] - (ImageFont.truetype(self._font, self._font_Player_Online_size).getlength(entry))) / 2)
                x = int(self._banner_shadow_box_x + center_align)
                self._draw_text((x,y), entry, self._font_Player_Online, self._font_Player_Online_color)
                y += self._font_Player_Online_text_height
  

