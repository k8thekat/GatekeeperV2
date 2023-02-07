#Banner Creator
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageColor
import pathlib
import random

import DB
import AMP_Handler
import logging
        
class Banner_Generator():
    """Custom Banner Generator for Gatekeeper. """
    def __init__(self, AMPServer:AMP_Handler.AMP.AMPInstance, DBBanner:DB.DBBanner, Banner_path:str=None, blur_background:bool=None):
        #Turn that str into a Purepath for cross OS support
        self._font = pathlib.Path("resources/fonts/ReemKufiFun-Regular.ttf").as_posix()
        self._logger = logging.getLogger()
        self._font_default_size = 25
        self._font_default = ImageFont.truetype(self._font, self._font_default_size)
        self._font_drop_shadow_size = (int(self._font_default_size / 5), int(self._font_default_size / 5))

        if Banner_path == None:
            Banner_path = AMPServer.background_banner_path
            if Banner_path == None:
                Banner_path = AMPServer.default_background_banner_path

        self._Server = AMPServer
        self._DBBanner = DBBanner

        self._banner_limit_size_x = 1800
        self._banner_limit_size_y = 600
        self.banner_image = self._validate_image(pathlib.Path(Banner_path).as_posix())

    
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

        self._font_Body_size = int(self._font_default_size * 2)
        self._font_Body_line_offset = 0
        self._font_Body_color = DBBanner.color_body #Off White
        # self._font_Body_color = "#f2f3f4" #Off White
        self._font_Body = ImageFont.truetype(self._font, self._font_Body_size)
        self._font_Body_text_height = self._font_Body.getbbox('W')[-1]

        self._font_Host_color = DBBanner.color_host
        # self._font_IP_color = "#5dade2"
        self._font_Host_size = int(self._font_default_size * 3)
        self._font_Host = ImageFont.truetype(self._font, self._font_Host_size)
        self._font_Host_text_height = self._font_Host.getbbox('W')[-1]

        self._font_Whitelist_size = int(self._font_default_size * 3.5)
        self._font_Whitelist_color_open =  DBBanner.color_whitelist_open
        self._font_Whitelist_color_closed = DBBanner.color_whitelist_closed
        # self._font_Whitelist_color_open =  "#f7dc6f"
        # self._font_Whitelist_color_closed = "#cb4335"
        self._font_Whitelist = ImageFont.truetype(self._font, self._font_Whitelist_size)
        self._font_Whitelist_text_height = self._font_Whitelist.getbbox('W')[-1]

        self._font_Donator_size = int(self._font_default_size * 3.5)
        self._font_Donator_color = DBBanner.color_donator
        # self._font_Donator_color = "#212f3c"
        self._font_Donator = ImageFont.truetype(self._font, self._font_Donator_size)
        self._font_Donator_text_height = self._font_Donator.getbbox('W')[-1]

        
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

        #If Whitelisting is NOT Disabled display Whitelist Text.
        if not AMPServer.Whitelist_disabled:
            self._Server_Whitelist()
        
        #If Donator Only; display the Text
        if AMPServer.Donator:
            self._Server_Donator()

        self._Server_Description()
        self._Server_Players_Online()
        self._Server_Host()
        #This MUST BE CALLED LAST
        self._round_corners()

    def _image_(self):
        return self.banner_image

    def _validate_image(self, path) -> Image.Image:
        try:
            image = Image.open(path)

            image = image.resize(size=(self._banner_limit_size_x, self._banner_limit_size_y), resample= Image.Resampling.BICUBIC)

            if image.mode != 'RGBA':
                image = image.convert(mode= 'RGBA')
            return image
        except:
            #We are reverting all changes to default values due to failure.
            self._logger.error(f'We Failed to find the Existing Image Path, resetting {self._Server.InstanceName} background path to default.')
            self._Server.background_banner_path = self._Server.default_background_banner_path
            self._DBBanner.background_path = self._Server.default_background_banner_path 
            return self._validate_image(path= self._Server.default_background_banner_path)

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
        #Lets truncate our Display Name since; well it can clip the shadowbox..
        name = self._word_wrap(name, self._font, self._font_Header_size, (self._banner_shadow_box_x - x), ' ')
        self._draw_text((x,y), name, self._font_Header, self._font_Header_color)
    
    def _Server_Host(self):
        self._font_Host_y = self._font_Header_text_height + self._font_Body_text_height + 5
        if self._Server.Host not in [None, '', 'None']:
            text = 'Host: ' + self._Server.Host #offset = int(ImageFont.truetype(self._font, self._font_Host_size).getlength(text)/2)
    
            x,y = (25, self._font_Host_y)
            self._draw_text((x,y), text, self._font_Host, self._font_Host_color)

    def _Server_Whitelist(self):
        self._font_Whitelist_y = int(self._font_Header_text_height  + self._font_Host_text_height + self._font_Whitelist_text_height + 5)
        text = 'Whitelist Closed'
        color = self._font_Whitelist_color_closed
        shadow_color = None

        if self._Server.Whitelist == 1 and self._Server.ADS_Running != 0:
            text = 'Whitelist Open'
            color = self._font_Whitelist_color_open

        offset = ImageFont.truetype(self._font, self._font_Whitelist_size).getlength(text)
        x,y = (int(self._center_align_Body - (offset / 2)), self._font_Whitelist_y)
        self._draw_text((x,y), text= text, font= self._font_Whitelist, fill= color, drop_shadow_fill= shadow_color)
    
    def _Server_Donator(self):
        #Location
        self._font_Donator_y = int(self._font_Whitelist_y + self._font_Whitelist_text_height)
        text = '[Donator Only]'
        color = self._font_Donator_color
        shadow_color = '#3498db'
        offset = ImageFont.truetype(self._font, self._font_Donator_size).getlength(text)
        x,y = (int(self._center_align_Body - (offset / 2)), self._font_Donator_y)
        self._draw_text((x,y), text= text, font= self._font_Donator, fill= color, drop_shadow_fill= shadow_color)
        
    def _Server_Description(self):
        x,y= (100, (self._font_Header_text_height + 10))

        if self._Server.Description != None:
            text = self._word_wrap(self._Server.Description, self._font, self._font_Body_size, (self._banner_shadow_box_x - x), ' ', True)
            if type(text) == list:
                for entry in text:
                    self._draw_text((x,y), entry, self._font_Body, self._font_Body_color)
                    x = x
                    y += self._font_Body_text_height
            else:
                self._draw_text((x,y), text, self._font_Body, self._font_Body_color)

  
    def _Server_Status(self):
        text = 'Offline'
        fill = self._font_Status_color_offline
        padding = int((self._banner_shadow_box[0] - self._font_Status_text_length_Offline) / 2)
        if self._Server.ADS_Running == 1:
            text = 'Online: '
            fill = self._font_Status_color_online
            #This will change depending on the player limit of the server.
            self.user_count = self._Server.getUsersOnline()
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
  
# test_path = 'resources/banners/Minecraft_banner2.jpg'
# server = fake_server()
# banner = fake_banner()
# a = Banner_Generator(AMPServer= server, DBBanner= banner, Banner_path= test_path)
# #a._image_().save(fp= "dev/test.png", format= 'PNG')
# a._image_().show()