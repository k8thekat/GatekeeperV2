#Banner Creator
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageColor
import pathlib

import random

class fake_server():
    def __init__(self):
        self.DisplayName = 'All The Mods 7: To The Sky'
        self.Description = 'All the Mods 7 To the Sky is the sequel to the popular atm6 sky, we have taken feedback from the first iteration to make this pack the best we have to offer, adding in mods that were not in the first, such as Twilight Forest and Alchemistry, followed by the mod ex machinis, an automation addon for ex nihilo built in house by ATM to take you from early, all the way to end game automated resources.'
        self.IP = '192.168.3.50:25565'
        self.Whitelist = random.randint(0,1)
        self.Donator = random.randint(0,1)
        self.Status = random.randint(0,1)
        self.Player_Limit = random.randint(0,20)
        self.Players_Online = ['k8_thekat', 'Lightning', 'Alain', 'Dann', 'Saorie', 'IceofWraith', 'BigO','Steve','k8_thekat', 'Lightning', 'Alain', 'Dann', 'Saorie', 'IceofWraith', 'BigO','Steve']
        self.Nicknames = ['ATM7 Sky', 'ATM7SKY','ATM7 to the Sky', 'All the Mods 7: Sky', 'ATM7:Sky', 'All The Mods 7: To the Sky']

class Banner_Generator():
    """Custom Banner Generator for Gatekeeper. """
    def __init__(self, Banner_path:str, AMPServer:fake_server, blur_background=True):
        
        self._font = pathlib.Path("resources/fonts/ReemKufiFun-Regular.ttf").as_posix()
        #Turn that str into a Purepath for cross OS support
        self.banner_image = self._validate_image(pathlib.Path(Banner_path).as_posix())
        self._font_default = ImageFont.truetype(self._font, 25)

        self._Server = AMPServer
        if blur_background:
            self._blur_background()

        self._banner_limit_size_y = 300
        self._banner_limit_size_x = 1300

        self._banner_shadow_box = (300,300)
        self._banner_shadow_box_x = self._banner_limit_size_x - self._banner_shadow_box[0]

        self._center_align_Body = int(((self._banner_limit_size_x - self._banner_shadow_box[0]) /2))

        self._font_Header_size = 60
        self._font_Header_color =  "#85c1e9" #Really light Blue
        self._font_Header = ImageFont.truetype(self._font, self._font_Header_size)
        self._font_Header_text_height = self._font_Header.getsize('W')[1]

        self._font_Nickname_size = 25
        self._font_Nickname_color = "#f2f3f4"
        self._font_Nickname = ImageFont.truetype(self._font, self._font_Nickname_size)
        self._font_Nickname_text_height = self._font_Nickname.getsize('W')[1]

        self._font_Body_size = 25
        self._font_Body_line_offset = 0
        self._font_Body_color = "#f2f3f4" #Off White
        self._font_Body = ImageFont.truetype(self._font, self._font_Body_size)
        self._font_Body_text_height = self._font_Body.getsize('W')[1]

        self._font_IP_color = "#5dade2"
        self._font_IP_size = 35
        self._font_IP = ImageFont.truetype(self._font, self._font_IP_size)
        self._font_IP_text_height = self._font_IP.getsize('W')[1]

        self._font_Whitelist_Donator_size = 45
        self._font_Whitelist_color_open =  "#f7dc6f"
        self._font_Whitelist_color_closed = "#cb4335"
        self._font_Donator_color = "#212f3c"
        self._font_Whitelist_Donator = ImageFont.truetype(self._font, self._font_Whitelist_Donator_size)
        self._font_Whitelist_Donator_text_height = self._font_Whitelist_Donator.getsize('W')[1]
        
        self._font_Status_size = 45
        self._font_Status = ImageFont.truetype(self._font, self._font_Status_size)
        self._font_Status_text_height = self._font_Status.getsize('W')[1]

        self._font_Status_color_online = "#28b463" #Green
        self._font_Status_text_length_Online = self._font_Status.getsize('Online: ')[0]

        self._font_Status_color_offline =  "#e74c3c" #Red
        self._font_Status_text_length_Offline = self._font_Status.getsize('Offline')[0]

        self._font_Player_Limit_size = 25
        self._font_Player_Limit_color_max = "#ba4a00"
        self._font_Player_Limit_color_min = "#5dade2"
        self._font_Player_Limit = ImageFont.truetype(self._font, self._font_Player_Limit_size)
        self._font_Player_Limit_text_height = self._font_Player_Limit.getsize('W')[1]

        self._font_Player_Online_size = 25
        self._font_Player_Online_color = "#f7dc6f" #white
        self._font_Player_Online = ImageFont.truetype(self._font, self._font_Player_Online_size)
        self._font_Player_Online_text_height = self._font_Player_Online.getsize('W')[1]
        
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

    def _validate_image(self, path)-> Image.Image:
        try:
            image = Image.open(path)
            return image
        except:
            raise

    def _blur_background(self):
        self.banner_image = self.banner_image.filter(ImageFilter.GaussianBlur(2))
        return 

    def _word_wrap(self, text:str, text_font:ImageFont.ImageFont, text_size:int, limit:int, find_char:str, truncate:bool=True):
        """Custom Word Wrap. \n
        Returns a `list` when `truncate` is `False`"""
        if text.find(find_char) == -1:
            return None

        split_test_str = text.split(find_char)
        temp_list = []
        temp_str = ''
        for i in range(0,len(split_test_str)):
            cur_str = temp_str
            temp_str += split_test_str[i] + find_char
            if ImageFont.truetype(text_font, text_size).getsize(temp_str)[0] < limit:
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
        if self._Server.Player_Limit == 0:
            return min_rgb

        for color in range(0,len(min_rgb)):
            temp_rgb = min_rgb[color] - max_rgb[color]
            temp_rgb/= self._Server.Player_Limit
            temp_rgb*= players_online
            temp_rgb += min_rgb[color]
            final_rgb[color] = int(temp_rgb)
        return tuple(final_rgb)

    def _round_corners(self):
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

        image_size = font.getsize(text=text)
        shadow = Image.new('RGBA', [image_size[0]+3,image_size[1]+3])
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.text(xy=(3,3), text= text, fill= drop_shadow_fill, font= font)
        shadow = shadow.filter(ImageFilter.GaussianBlur(drop_shadow_blur))

        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.text(xy=(0,0), text= text, fill= fill, font= font)

        self.banner_image.paste(shadow, xy, mask= shadow)

    def _shadow_box(self):
        box = Image.new('RGBA', [self._banner_shadow_box[0]+10, self._banner_shadow_box[1]])
        box_draw = ImageDraw.Draw(box)
        box_draw.rounded_rectangle([(10,0), (self._banner_shadow_box[0]+10, self._banner_shadow_box[1])], radius= 40, fill= (0,0,0,175))
        box = box.filter(ImageFilter.GaussianBlur(2))
        self.banner_image.paste(box, (self._banner_shadow_box_x, 0), mask= box)

    def _Server_Name(self):
        x,y = 25,0
        self._draw_text((x,y),self._Server.DisplayName, self._font_Header, self._font_Header_color)
    
    def _Server_NickNames(self):
        self._font_Nicknames_y = self._font_Header_text_height + 5
        if len(self._Server.Nicknames) > 0:
            x,y = (50, self._font_Nicknames_y)
            text = "Nicknames: " + " , ".join(self._Server.Nicknames)
            text = self._word_wrap(text, self._font, self._font_Nickname_size, (self._banner_shadow_box_x - x), ',' , True )
            self._draw_text((x,y), text, self._font_Nickname, self._font_Nickname_color)

    def _Server_IP(self):
        self._font_IP_y = self._font_Nicknames_y + self._font_Body_text_height
        if self._Server.IP != None or self._Server.IP != '':
            text = 'Host: ' + self._Server.IP
            offset = int(ImageFont.truetype(self._font, self._font_IP_size).getsize(text)[0]/2)
    
            x,y = (25, self._font_IP_y)
            self._draw_text((x,y), text, self._font_IP, self._font_IP_color)

    def _Server_Whitelist_Donator(self):
        self._font_Whitelist_Donator_y = self._font_Header_text_height + 5 + self._font_Body_text_height + 60
        text = 'Whitelist Closed'
        color = self._font_Whitelist_color_closed

        offset = ImageFont.truetype(self._font, self._font_Whitelist_Donator_size).getsize(text)[0]
        if self._Server.Whitelist == 1 and self._Server.Status != 0:
            text = 'Whitelist Open'
            color = self._font_Whitelist_color_open

            if self._Server.Donator == 1:
                offset = ImageFont.truetype(self._font, self._font_Whitelist_Donator_size).getsize(text)[0]
                text_donator = ' - [Donator Only]'
                self._draw_text((self._center_align_Body, self._font_Whitelist_Donator_y), text_donator, self._font_Whitelist_Donator, self._font_Donator_color, "#3498db")

        x,y = (self._center_align_Body - offset, self._font_Whitelist_Donator_y)
        self._draw_text((x,y), text, self._font_Whitelist_Donator, color)

    def _Server_Description(self):
        x,y= (15, (self._banner_limit_size_y - (self._font_Body_text_height * 2) - 8))
  
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
        if self._Server.Status == 1:
            text = 'Online: '
            fill = self._font_Status_color_online
            #This will change depending on the player limit of the server.
            text_length = ImageFont.truetype(self._font, self._font_Status_size).getsize(text + str(self._Server.Player_Limit) + "/20" )[0]
            padding = int((self._banner_shadow_box[0] - text_length) / 2)

            y = 0
            x = (self._banner_shadow_box_x + padding + self._font_Status_text_length_Online)
            self._draw_text((x,y), str(self._Server.Player_Limit) + "/20", self._font_Status, self._color_gradient())

        x,y = ((self._banner_shadow_box_x + padding), 0)
        self._draw_text((x,y), text, self._font_Status, fill)

    def _Server_Players_Online(self):
        index = 0
        if self._Server.Status != 0:
            y = self._font_Status_text_height
            for entry in self._Server.Players_Online:
                if index > 8:
                    return
                index += 1
                center_align = int((self._banner_shadow_box[0] - (ImageFont.truetype(self._font, self._font_Player_Online_size).getsize(entry))[0]) / 2)
                x = self._banner_shadow_box_x + center_align
                self._draw_text((x,y), entry, self._font_Player_Online, self._font_Player_Online_color)
                y += self._font_Player_Online_text_height
  
image = "resources/banners/Untitled-1.png"
a = Banner_Generator(image, fake_server())
a.banner_image.show()
