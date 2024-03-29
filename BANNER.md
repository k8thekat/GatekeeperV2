# **Banner**
Welcome to Gatekeepers Display Banners page. In this section we will cover how to use and interact with Gatekeepers Banners.

Need color hex codes? [Color Hex](https://www.color-hex.com/)
___

## **What is a Banner?**
___
Well Gatekeeper currently has two formats, `Discord Embeds` or `Custom Banner Images`. Both of which display the same information; the main difference is the appearance.  
**Discord Embed**  
![embed](/resources/wiki/banner/embed_example.png)

**Custom Banner Images**  
![custom](/resources/wiki/banner/custom_banner_example.png)



## **Editing your Server Banner/Embed**
___
Most of the settings will be handles via [Server Setting Commands](/COMMANDS.md#amp-server-settings-commands); these usually include your `Host`, `Whitelist` and `Donator`.  
- **TIP**: `Description` is using your AMP Instance Description. [What is this?](/resources/wiki/banner/banner_description_location.png)

### Using the Custom Banner Image Editor:  
- This section is used for editing `Custom Banner Images`; you must enable them via `/bot banner_settings` and for the field `type` select `Custom Banner Images`.  
- **TIP**: Use `Blur Background Intensity` to help with text readability by bluring the background. Default is `0`

- Below you will see an example picture of Gatekeepers `Banner Editor` looks like.
    - Each section of text is unique and can have a different color than each other. See below~

![editor](/resources/wiki/banner/banner_editor_example.png)

- Here is what your `Header Font Color` will affect.   

![header](/resources/wiki/banner/header_example.png)

- Here is what `Host Font Color` will affect.  

![host](/resources/wiki/banner/host_example.png)

- Here is what `Body Font Color` will affect.

![body](/resources/wiki/banner/description_example.png)


- Here is what `Server Online Font Color` when the server is Online or `Server Offline Font Color` when it is Offline.  
    -  `Player Limit Minimum Font Color` and `Player Limit Maximum Font Color` is your min and max color hex values.
    - As the player count increases the `Font Color` gradient will move towards the `Player Limit Maximum Font Color` and as the player count decreases the `Font Color` will gradient towards `Player Limit Minimum Font Color`.
    - A `0` count of players online will use `Player Limit Minimum Font Color` and at player limit will use `Player Limit Maximum Font Color`.  
    - The player name below `Online` will use `Players Online Font Color`

![status](/resources/wiki/banner/status_example.png)



- Here is what `Whitelist Open Font Color`, `Whitelist Closed Font Color` and `Donator Font Color` will affect.

![whitelist_donator](/resources/wiki/banner/whitelist_donator_example.png)


## **How to Display your Banners**
___
Cool you have probably figured out how to edit your banners and make them look how you want; but you still cant see them anywhere yet. Let's start!

Full list of commands -> [Banner Group commands](/COMMANDS.md#bot-bannergroup-commands)

1. First we need to create a `Banner Group` use `/bot bannergroup create_group` and enter a group name *(eg. Minecraft)*
    - The name you enter is for identifcation purposes only. Autocomplete will prompt all group names.
2. Next we need to do is use `/bot bannergroup add` and select the group you recently made in step 1, then select the `server` parameter and choose a server from the auto complete to add it to the group.
3. Next we use the same command `/bot bannergroup add` and select the group you recently made. Now this time we select `channel` and pick a channel from the autocomplete. This is where the banner will show up.
    - **TIP** - You can add a `server` and a `channel` at the same time.
    - The bot must be able to **send, edit and delete messages** in this channel. *Failure to have permissions will cause unexpected results.*
4. Tada; give it a moment to populate. Shortly you should see a Banner Image or Embed be displayed in the channel you selected with the server you added to group you made in step 1.
