
    def user_info_embed(self, db_user:DB.DBUser, discord_user:discord.User)-> discord.Embed:
        embed=discord.Embed(title=f'{discord_user.name}',description=f'**Discord ID**: {discord_user.id}', color=discord_user.color)
        embed.set_thumbnail(url= discord_user.avatar.url)
        embed.add_field(name='In Database:', value=f'{"True" if db_user != None else "False"}')
        if db_user != None:
            if db_user.MC_IngameName != None:
                embed.add_field(name='Minecraft IGN:', value=f'{db_user.MC_IngameName}', inline= False)

            if db_user.MC_UUID != None:
                embed.add_field(name='Minecraft UUID:', value=f'{db_user.MC_UUID}', inline= True)

            if db_user.SteamID != None:
                embed.add_field(name='Steam ID:', value=f'{db_user.SteamID}', inline=False)

            if db_user.Role != None:
                embed.add_field(name='Permission Role:', value=f'{db_user.Role}', inline=False)
                
        return embed