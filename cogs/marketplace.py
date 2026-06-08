import discord
from discord.ext import commands
from discord import app_commands


# Button
class marketplace_buttons(discord.ui.View):
    def __init__(self, channel: discord.TextChannel, embed: discord.Embed):
        self.channel = channel
        self.embed = embed
        self.cooldown = commands.CooldownMapping.from_cooldown(1, 300.0, commands.BucketType.user)
        super().__init__()

    # Post button
    @discord.ui.button(label="Post", style=discord.ButtonStyle.green)
    async def on_click_post(self, interaction: discord.Interaction, button: discord.ui.Button):
        interaction.message.author = interaction.user
        retry_after = self.cooldown.get_bucket(interaction.message).update_rate_limit()

        if retry_after:
            return await interaction.response.send_message(f"You're on cooldown, try again in {round(retry_after)} seconds!", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        await self.channel.send(embed=self.embed)
        await interaction.followup.send("Your post has been sent in the respective channel", ephemeral=True)

    # Delete button
    @discord.ui.button(label="Delete preview", style=discord.ButtonStyle.red)
    async def on_click_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await interaction.delete_original_response()

# For-hire modal
class forhire_modal(discord.ui.Modal):
    def __init__(self, channel: discord.TextChannel):
        self.channel = channel
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

        view = marketplace_buttons(channel=self.channel, embed=embed)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# Hire modal
class hire_modal(discord.ui.Modal):
    def __init__(self, channel: discord.TextChannel):
        self.channel = channel
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
    async def on_submit(self, interaction: discord.Interaction):
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

        view = marketplace_buttons(embed=embed, channel=self.channel)
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
    @app_commands.checks.cooldown(1, 3600.0, key=lambda i: (i.guild_id, i.user.id))
    async def forhire_post(self, interaction: discord.Interaction, channel: discord.TextChannel):
        modal = forhire_modal(channel=channel)
        await interaction.response.send_modal(modal)

    # Hire command
    @app_commands.command(name="hire", description="Send a hire post in a channel")
    @app_commands.checks.bot_has_permissions(send_messages=True)
    @app_commands.checks.has_permissions(send_messages=True)
    @app_commands.describe(channel="Type a channel to send the post in")
    @app_commands.checks.cooldown(1, 3600.0, key=lambda i: (i.guild_id, i.user.id))
    async def hire_post(self, interaction: discord.Interaction, channel: discord.TextChannel):
        modal = hire_modal(channel=channel)
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

    # Error handler
    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(str(error), ephemeral=True)
        elif isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(str(error), ephemeral=True)
        elif interaction.response.is_done():
            await interaction.followup.send(str(error), ephemeral=True)
        else:
            await interaction.response.send_message(str(error), ephemeral=True)
        
    
async def setup(bot: commands.Bot):
    await bot.add_cog(marketplace_cog(bot))