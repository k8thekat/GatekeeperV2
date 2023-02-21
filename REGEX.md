# Regex
Welcome to Gatekeepers Regex section, In this section we will cover how to manage your Regex patterns with Gatekeeper.

Need to test your Regex? **[Regex Tester](https://regex101.com/)**

## What is a Regular Expression?
___
Regular Expression, or regex in short, is extremely and amazingly powerful in searching and manipulating text strings.
- See [PyDoc on Regex](https://docs.python.org/3/howto/regex.html).
- We do have a few examples down below [Examples](#examples).

## **How to Manage your Bot Regex Patterns**
___
This section covers the basic commands you will use to interact with Gatekeepers Regex Patterns.  
 - **TIP**: All Regex patterns can be used on multiple Servers.  

For starters lets cover how to `add` a Regex Pattern.
### ADD:
- The command to add a Regex Pattern is `/bot regex_pattern add (name, filter_type, pattern)`.
    - `name`: Must be unique. I suggest making it descriptive enough to tell them apart, I will explain why later.
    - `filter_type`: You have `Console` or `Events` to pick from which dictates which Discord Channel the message will go to.
    - `pattern`: This is where your Regular Expression goes. 

### DELETE:
- The command to delete a Regex Pattern is `/bot regex_pattern delete (name)`.
    - `name`: This field will auto populate with the names of Regex Patterns already in the Database.

### UPDATE:
- The command to update a Regex Pattern is `/bot regex_pattern update (name, new_name, filter_type, pattern)`.
    - `name`: This field will auto populate with the names of Regex Patterns already in the Database.
    - These next fields are all optional, you can change one or all 3 at the same time.
        - `new_name`: Must be unique and must not match the current `name`.
        - `filter_type`: Same as add; `Console` or `Events`.
        - `pattern`: This is where the "new" Regex pattern goes if you want to replace the existing one.

- Use Cases:
    - You have a pattern named `Minecraft` with the `filter_type` of `Console`. You want to change its `filter_type` to `Events`.
        - So we will use `/bot regex_pattern update`.
            - We select `Minecraft` for the `name` field. 
            - We select `Events` for the `filter_type` field.
            - Then hit Enter to submit and viola, Gatekeeper will reply with the updated information.
        

### LIST:
- The command to list all your Regex Patterns is `/bot regex_pattern list`.
    - Gatekeeper will reply with an Embed styled list and provide information regarding each Regex in the Database.  

![regex_list](/resources/wiki/regex/regex_list_example.png)


## **How to Manage your Servers Regex Patterns**
___
As you noticed with [Bot Regex Patterns](#how-to-manage-your-bot-regex-patterns) the `name` field auto populates with all your created Regex patterns for ease of navigation.
- This is why it can become important to uniquely name your patterns.
- **REMINDER**: Any Regex pattern you have added to a Server will update when you use `/bot regex_pattern update`
### ADD:
- The command to add a Regex Pattern to a Server is `/server regex add (server, name)`.
    - `server`: This field will auto populate with all your AMP Instances for selection.
    - `name`: This field will auto populate with all your Regex patterns from the Database.

### DELETE:
- The command to delete a Regex Pattern from a Server is `/server regex delete (server, name)`.
    - `server`: This field will auto populate with all your AMP Instances for selection.
    - `name`: This field will auto populate with all your Regex patterns from the Database.

### LIST:
- The command to list all Regex Patterns a Server is using is `/server regex list (server)`.
    - `server`: This field will auto populate with all your AMP Instances for selection.


## **How Console Filtering can affect your Regex Patterns**
___
### **When `/server console filter` has a filter_type = `Whitelist`**
- This means *ANY* matches to the Regex pattern will be captured and all other messages will be ommited.

![whitelist_example](/resources/wiki/regex/regex_whitelist_example.png)
- As you can see in the above example I created a **Pattern** named `Minecraft` with the **filter_type** set to `Console` (Referred to as **TYPE**) via `/bot regex_pattern add`. 
    - The **Regex pattern** is `(Player Console banned|You have been banned:|Player Console unbanned)`.
- You can see I added the **Pattern** named `Minecraft` to `TestServer01` then I set `TestServer01` Console filtering to `True` and set it to `Whitelist` via `/server console filter`.  
    - The result would be **ANY MATCH** to the pattern would be sent to `TestServer01` Console Channel.
___
Now here is another **Regex pattern** `"(left the game|joined the game|tried to swim|completed the challenge|made the advancement|was slain by|fell off|was shot by)"`. 
- We used `/bot regex_pattern add` and set the **filter_type** to `Events`.
- With the above pattern and settings previously shown in the above examples. The two boxed strings from that Servers Console would be output to Discord.  

![whitelist_example_3](/resources/wiki/regex/regex_whitelist_console_1.png)
___
### **When  `/server console filter` has a filter_type = `Blacklist`**
- This means *ANY* matches to the Regex pattern will be ommitted and all other messages will pass through.

![blacklist_example](/resources/wiki/regex/regex_blacklist_example.png)  
- As stated before; you can see I added the **PATTERN** named `whitelist` and set the **filter_type** to `Console`.
    - So any strings matching the **Regex Pattern** `(/whitelist)` will be ommited.
- You can still see it inside the AMP Console, but if you notice in the below example that Discord doesn't have the `/whitelist` entry.   

![blacklist_example_3](/resources/wiki/regex/regex_blacklist_comparison.png)  
___
## Examples

### **Minecraft:**
 - ```'(Unkown command|players online:|Staff|Help|left the game|joined the game|lost connection:|whitelisted players:|was slain by|game mode to)'```

 - ```'(Player Console banned|You have been banned:|Player Console unbanned)'```

 - ```'(Added|to the whitelist|Removed|from the whitelist)'```

 - ```'(left the game|joined the game|tried to swim|completed the challenge|made the advancement|was slain by|fell off|was shot by)'```
___