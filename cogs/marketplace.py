import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta, datetime


# Post deny modal
class post_deny_modal(discord.ui.Modal):
    def __init__(self, user: discord.Member, button: discord.ui.Button, view: discord.ui.View, bot: commands.Bot):
        self.user = user
        self.button = button
        self.view = view
        self.bot = bot
        super().__init__(title="Reason for denial")

    Reason = discord.ui.TextInput(
        label="Reason",
        required=True,
        style=discord.TextStyle.paragraph
    )

    # On modal submit
    async def on_submit(self, interaction: discord.Interaction):
        for item in self.view.children:
            item.disabled = True
        await interaction.response.edit_message(view=self.view)
        await interaction.response.send_message("Post denied", ephemeral=True)
        await self.user.send(f"{self.user.mention}, your post has been denied.\nReason: {self.Reason.value}")


# Post approve/deny buttons
class post_buttons(discord.ui.View):
    def __init__(self, embed: discord.Embed, user: discord.Member, bot: commands.Bot):
        self.embed = embed
        self.user = user
        self.bot = bot
        super().__init__(timeout=None)

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.green)
    async def on_approve_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        for item in self.children:
            item.disabled = True
        await interaction.edit_original_response(view=self)
        user = await self.bot.fetch_user(self.user)
        await user.send(f"{user.mention}, your post has been approved.")
        await interaction.followup.send("Post approved!", ephemeral=True)

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.red)
    async def on_deny_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(post_deny_modal(user=self.user, button=button, view=self, bot=self.bot))
        
# Button
class marketplace_buttons(discord.ui.View):
    def __init__(self, channel: discord.TextChannel, embed: discord.Embed, bot: commands.Bot):
        self.channel = channel
        self.embed = embed
        self.bot = bot
        # self.cooldown = commands.CooldownMapping.from_cooldown(1, 300.0, commands.BucketType.user)
        super().__init__()

    # Post button
    @discord.ui.button(label="Post", style=discord.ButtonStyle.green)
    async def on_click_post(self, interaction: discord.Interaction, button: discord.ui.Button):
        # interaction.message.author = interaction.user
        # retry_after = self.cooldown.get_bucket(interaction.message).update_rate_limit()

        # if retry_after:
        #     return await interaction.response.send_message(f"You're on cooldown, try again in {round(retry_after)} seconds!", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        await self.channel.send(embed=self.embed)
        await interaction.followup.send("Your post has been sent in the respective channel", ephemeral=True)

    # Delete button
    @discord.ui.button(label="Delete preview", style=discord.ButtonStyle.red)
    async def on_click_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await interaction.delete_original_response()

    # Approval button
    @discord.ui.button(label="Submit for approval", style=discord.ButtonStyle.green)
    async def on_click_approval(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        for item in self.children:
            item.disabled = True
        await interaction.edit_original_response(view=self)
        row = await self.bot.db.fetchrow("""
            SELECT * FROM set_approval WHERE guild_id = $1
            """,
            interaction.guild_id
        )
        channel = await self.bot.fetch_channel(row["channel_id"])
        await channel.send(embed=self.embed, view=post_buttons(embed=self.embed, user=interaction.user.id, bot=self.bot))
        await interaction.followup.send("Your post has been sent for approval", ephemeral=True)

cooldowns = {} 

# For-hire modal
class forhire_modal(discord.ui.Modal):
    def __init__(self, channel: discord.TextChannel, bot: commands.Bot):
        self.channel = channel
        self.bot = bot
        super().__init__(title="Tell us about yourself")

    About = discord.ui.TextInput(
        label="Description",
        required=True,
        style=discord.TextStyle.paragraph
    )

    Payment = discord.ui.TextInput(
        label="Payment",
        required=True,
        style=discord.TextStyle.paragraph
    )

    Contact = discord.ui.TextInput(
        label="Contact information",
        required=True,
        style=discord.TextStyle.paragraph
    )

    thumbnail = discord.ui.TextInput(
        label="Thumbnail url",
        required=False,
        style=discord.TextStyle.short
    )

    image = discord.ui.TextInput(
        label="Image url",
        required=False,
        style=discord.TextStyle.short
    )

    # On modal submit
    async def on_submit(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        current_time = datetime.now()
        last_used = cooldowns.get(user_id)

        if last_used and current_time - last_used < timedelta(hours=1):
            remaining = round((last_used + timedelta(hours=1) - current_time).total_seconds())
            return await interaction.response.send_message(f"You're on cooldown! Try again in {remaining}s.", ephemeral=True)

        cooldowns[user_id] = current_time
        embed = discord.Embed(
            title="For hire post",
            color=discord.Colour.green()
        )
        embed.add_field(name="Description", value=self.About.value, inline=False)
        embed.add_field(name="Payment", value=self.Payment.value, inline=False)
        embed.add_field(name="Contact", value=self.Contact.value, inline=False)
        if self.thumbnail.value:
            embed.set_thumbnail(url=self.thumbnail.value)
        if self.image.value:
            embed.set_image(url=self.image.value)

        view = marketplace_buttons(channel=self.channel, embed=embed, bot=self.bot)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# Hire modal
class hire_modal(discord.ui.Modal):
    def __init__(self, channel: discord.TextChannel, bot: commands.Bot):
        self.channel = channel
        self.bot = bot
        super().__init__(title="Tell us what you're looking for")

    About = discord.ui.TextInput(
        label="Description",
        required=True,
        style=discord.TextStyle.paragraph
    )

    Payment = discord.ui.TextInput(
        label="Payment",
        required=True,
        style=discord.TextStyle.paragraph
    )

    Contact = discord.ui.TextInput(
        label="Contact information",
        required=True,
        style=discord.TextStyle.short
    )

    thumbnail = discord.ui.TextInput(
        label="Thumbnail url",
        required=False,
        style=discord.TextStyle.short
    )

    image = discord.ui.TextInput(
        label="Image url",
        required=False,
        style=discord.TextStyle.short
    )

    # On modal submit
    async def on_submit_hire(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        current_time = datetime.now()
        last_used = cooldowns.get(user_id)

        if last_used and current_time - last_used < timedelta(hours=1):
            remaining = round((last_used + timedelta(hours=1) - current_time).total_seconds())
            return await interaction.response.send_message(f"You're on cooldown! Try again in {remaining}s.", ephemeral=True)

        cooldowns[user_id] = current_time
        embed = discord.Embed(
            title="Hire post",
            color=discord.Colour.green()
        )
        embed.add_field(name="Description", value=self.About.value, inline=False)
        embed.add_field(name="Payment", value=self.Payment.value, inline=False)
        embed.add_field(name="Contact information", value=self.Contact.value, inline=False)
        if self.thumbnail.value:
            embed.set_thumbnail(url=self.thumbnail.value)
        if self.image.value:
            embed.set_image(url=self.image.value)

        view = marketplace_buttons(embed=embed, channel=self.channel, bot=self.bot)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# The main cog
class marketplace_cog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        super().__init__()

    # For-hire command
    @app_commands.command(name="forhire", description="Send a for hire post in a channel")
    @app_commands.checks.bot_has_permissions(send_messages=True)
    @app_commands.checks.has_permissions(send_messages=True)
    @app_commands.describe(channel="Type a channel to send the post in")
    async def forhire_post(self, interaction: discord.Interaction, channel: discord.TextChannel):
        modal = forhire_modal(channel=channel, bot=self.bot)
        await interaction.response.send_modal(modal)

    # Hire command
    @app_commands.command(name="hire", description="Send a hire post in a channel")
    @app_commands.checks.bot_has_permissions(send_messages=True)
    @app_commands.checks.has_permissions(send_messages=True)
    @app_commands.describe(channel="Type a channel to send the post in")
    @app_commands.checks.cooldown(1, 3600.0, key=lambda i: (i.guild_id, i.user.id))
    async def hire_post(self, interaction: discord.Interaction, channel: discord.TextChannel):
        modal = hire_modal(channel=channel, bot=self.bot)
        await interaction.response.send_modal(modal)

    # Review command
    @app_commands.command(name="review", description="Leave a review to a developer")
    @app_commands.checks.bot_has_permissions(send_messages=True)
    @app_commands.checks.has_permissions(send_messages=True)
    @app_commands.describe(username="The username of the developer you wish to leave a review for", review="Your review")
    @app_commands.checks.cooldown(1, 300.0, key=lambda i: (i.guild_id, i.user.id))
    async def send_review(self, interaction: discord.Interaction, username: discord.Member, *, review: str):
        await interaction.response.defer(ephemeral=True)
        await self.bot.db.execute("""
            INSERT INTO reviews (username, review) VALUES ($1, $2)
            """,
            username.id, review
        )

        user = await self.bot.fetch_user(username.id)
        member = interaction.user

        await user.send(f"{member.mention} left a review! - {review}")
        await interaction.followup.send("Your review has been sent.", ephemeral=True)

    # Check review command
    @app_commands.command(name="checkreview", description="Check your reviews")
    @app_commands.checks.has_any_role('Developer')
    async def check_review(self, interaction: discord.Interaction, username: discord.Member):
        await interaction.response.defer(ephemeral=True)
        row = await self.bot.db.fetch("""
            SELECT * FROM reviews WHERE username = $1
            """,
            username.id
        )
        embed = discord.Embed(
            title="Your reviews",
            color=discord.Colour.green()
        )
        for no, record in enumerate(row, start=1):
            embed.add_field(name=f"Review#{no}", value=record["review"], inline=False)

        await interaction.followup.send(embed=embed, ephemeral=True)

    # Set approval channel where posts are supposed to be approved by mods
    @app_commands.command(name="setapproval", description="Set the post approval channel")
    @app_commands.checks.bot_has_permissions(manage_messages=True)
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.describe(channel="Channel to set")
    async def set_approval_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)
        await self.bot.db.execute("""
            INSERT INTO set_approval (guild_id, channel_id) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET channel_id = $2                       
            """,
            interaction.guild_id, channel.id
        )
        await interaction.followup.send(f"{channel.mention} has been set as approval channel.", ephemeral=True)


    # Error handler
    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(str(error), ephemeral=True)
        elif isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(str(error), ephemeral=True)
        elif isinstance(error, app_commands.CommandNotFound):
            await interaction.response.send_message(str(error), ephemeral=True)
        elif isinstance(error, app_commands.MissingRole):
            await interaction.response.send_message(str(error), ephemeral=True)
        elif interaction.response.is_done():
            await interaction.followup.send(str(error), ephemeral=True)
        else:
            await interaction.response.send_message(str(error), ephemeral=True)
        
    
async def setup(bot: commands.Bot):
    await bot.add_cog(marketplace_cog(bot))