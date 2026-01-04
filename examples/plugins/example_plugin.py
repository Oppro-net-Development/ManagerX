"""
This Cog loads the functions from the PyPI plugin
and exposes them as Discord commands.
"""

from discord.ext import commands
from managerx_example_plugin import (
    hello,
    add_numbers,
    multiply_numbers,
    format_user_message,
    current_time,
    is_even
)

class ExamplePlugin(commands.Cog):
    """Example Cog that uses the ManagerX Example Plugin functions."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="sayhello")
    async def say_hello(self, ctx):
        user = ctx.author.name
        result = hello(user)
        await ctx.send(result)

    @commands.command(name="add")
    async def add(self, ctx, a: int, b: int):
        result = add_numbers(a, b)
        await ctx.send(f"{a} + {b} = {result}")

    @commands.command(name="multiply")
    async def multiply(self, ctx, a: int, b: int):
        result = multiply_numbers(a, b)
        await ctx.send(f"{a} × {b} = {result}")

    @commands.command(name="formatmsg")
    async def formatmsg(self, ctx, *, message: str):
        user = ctx.author.name
        formatted = format_user_message(user, message)
        await ctx.send(formatted)

    @commands.command(name="time")
    async def time(self, ctx):
        await ctx.send(f"Current time: {current_time()}")

    @commands.command(name="iseven")
    async def is_even_cmd(self, ctx, number: int):
        result = is_even(number)
        await ctx.send(f"{number} is even? {result}")

# Setup function for bot
async def setup(bot):
    await bot.add_cog(ExamplePlugin(bot))