'''
MIT License

Copyright (c) 2017 Grok

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

import discord
from discord.ext import commands
from discord.ext.commands import TextChannelConverter
from contextlib import redirect_stdout
import traceback
import textwrap
import aiohttp
import inspect
import re
import io

dev_list = [
    180314310298304512,
    299357465236078592,
    227620842903830528,
    168143064517443584,
    273381165229146112,
    319395783847837696,
    323578534763298816
]

class Developer:
    '''Useful commands to make your life easier'''
    def __init__(self, bot):
        self.bot = bot
        #self.lang_conv = load_json('data/langs.json')
        self._last_embed = None
        self._rtfm_cache = None
        self._last_google = None
        self._last_result = None

    @commands.command(aliases=["reload"])
    async def reloadcog(self, ctx, *, cog:str):
        """Reloads a cog"""
        if ctx.author.id in dev_list:
            cog = "cogs.{}".format(cog)
            await ctx.send("Attempting to reload {}...".format(cog))
            self.bot.unload_extension(cog)
            try:
                self.bot.load_extension(cog)
                await ctx.send("Successfully reloaded the {} cog!".format(cog))
            except Exception as e:
                await ctx.send(f"```py\nError loading cog: {cog}\n{e}\n```")


    @commands.command(pass_context=True, hidden=True, name='eval')
    async def _eval(self, ctx, *, body: str):
        """Evaluates a code"""
        if ctx.author.id in dev_list:
            env = {
                'bot': self.bot,
                'ctx': ctx,
                'channel': ctx.channel,
                'author': ctx.author,
                'guild': ctx.guild,
                'message': ctx.message,
                '_': self._last_result
            }

            env.update(globals())

            body = self.cleanup_code(body)

            stdout = io.StringIO()
            err = out = None

            to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

            try:
                exec(to_compile, env)
            except Exception as e:
                err = await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')
                return await err.add_reaction('\u2049')

            func = env['func']
            try:
                with redirect_stdout(stdout):
                    ret = await func()
            except Exception as e:
                value = stdout.getvalue()
                err = await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
            else:
                value = stdout.getvalue()
                if self.bot.token in value:
                    value = value.replace(self.bot.token,"[EXPUNGED]")
                if ret is None:
                    if value:
                        try:
                            out = await ctx.send(f'```py\n{value}\n```')
                        except:
                            out = await ctx.send('Result was too long to send.')
                else:
                    self._last_result = ret
                    try:
                        out = await ctx.send(f'```py\n{value}{ret}\n```')
                    except:
                        out = await ctx.send('Result was too long to send.')

            if out:
                to_log = self.cleanup_code(out.content)
                await out.add_reaction('\u2705')
            elif err:
                to_log = self.cleanup_code(err.content)
                await err.add_reaction('\u2049')
            else:
                to_log = 'No textual output.'
                await ctx.message.add_reaction('\u2705')

            await self.log_eval(ctx, body, out, err)


    async def log_eval(self, ctx, body, out, err):
        if out:
            to_log = self.cleanup_code(out.content)
            color = discord.Color.green()
            name = 'Output'
        elif err:
            to_log = self.cleanup_code(err.content)
            color = discord.Color.red()
            name = 'Error'
        else:
            to_log = 'No textual output.'
            color = discord.Color.gold()
            name = 'Output'

        to_log = to_log.replace('`','\u200b`')

        em = discord.Embed(color=color,timestamp=ctx.message.created_at)
        em.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
        em.add_field(name='Input', value=f'```py\n{body}\n```', inline=False)
        em.add_field(name=name, value=f'```{to_log}```')
        em.set_footer(text=f'User ID: {ctx.author.id}')

        await self.bot.get_channel(362574671905816576).send(embed=em)



    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n')

    @commands.command()
    async def set_val(self, ctx, field, *, value):
        self.bot.db.set_value(ctx.server.id, field, value)
        await ctx.send(f'Updated `{field}` to `{value}`')

    @commands.command()
    async def get_val(self, ctx, field):
        value = self.bot.db.get_value(ctx.guild.id, field)
        await ctx.send(f'Value for `{field}`: `{value}`')

def setup(bot):
    bot.add_cog(Developer(bot))
