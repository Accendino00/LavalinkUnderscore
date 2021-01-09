from discord.ext import commands
import lavalink
from discord import utils
from discord import Embed

class MusicCog(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.bot.music = lavalink.Client(self.bot.user.id)
    self.bot.music.add_node('localhost', 7000, 'testing2', 'eu', 'music-node')
    self.bot.add_listener(self.bot.music.voice_update_handler, 'on_socket_response')
    self.bot.music.add_event_hook(self.track_hook)

  @commands.command(name='join')
  async def join(self, ctx):
    print('join command worked')
    member = utils.find(lambda m: m.id == ctx.author.id, ctx.guild.members)
    if member is not None and member.voice is not None:
      vc = member.voice.channel
      player = self.bot.music.player_manager.create(ctx.guild.id, endpoint=str(ctx.guild.region))
      '''if not player.is_connected:''' # codice originale
      player.store('channel', ctx.channel.id)
      await self.connect_to(ctx.guild.id, str(vc.id))

  @commands.command(name='play')
  async def play(self, ctx, *, query):
    
    member = utils.find(lambda m: m.id == ctx.author.id, ctx.guild.members)
    if member is not None and member.voice is not None:
      vc = member.voice.channel
      player = self.bot.music.player_manager.create(ctx.guild.id, endpoint=str(ctx.guild.region))
      if not player.is_connected:
        player.store('channel', ctx.channel.id)
        await self.connect_to(ctx.guild.id, str(vc.id))
    try:
      player = self.bot.music.player_manager.get(ctx.guild.id)
      query = f'ytsearch:{query}'
      results = await player.node.get_tracks(query)
      tracks = results['tracks'][0:10]
      i = 0
      query_result = ''
      for track in tracks:
        i = i + 1
        query_result = query_result + f'{i}) {track["info"]["title"]} - {track["info"]["uri"]}\n'
      embed = Embed()
      embed.description = query_result

      await ctx.channel.send(embed=embed)

      def check(m):
        return m.author.id == ctx.author.id
      
      response = await self.bot.wait_for('message', check=check)
      track = tracks[int(response.content)-1]

      player.add(requester=ctx.author.id, track=track)
      if not player.is_playing:
        await player.play()
      if player.queue:
        embed = Embed()
        embed.description = 'La tua canzone è in posizione: ' + str(len(player.queue))
        await ctx.channel.send(embed=embed)

    except Exception as error:
      print(error)
  

  @commands.command(name='stop')
  async def stop(self, ctx):
    player = self.bot.music.player_manager.get(ctx.guild.id)
    if player.is_playing:
      embed = Embed()
      embed.description = 'Mi hai fatto svenire col tuo Haki del Re Conquistatore!!!'
      await ctx.channel.send(embed=embed)
      await player.stop()


  @commands.command(name='skip')
  async def skip(self, ctx):
    player = self.bot.music.player_manager.get(ctx.guild.id)
    if player.is_playing:
      embed = Embed()
      embed.description = 'Hai usato la tua Vivre Card per skippare la canzone.'
      await ctx.channel.send(embed=embed)
      await player.skip()

  @commands.command(name='pause')
  async def set_pause(self, ctx):
    player = self.bot.music.player_manager.get(ctx.guild.id)
    if player.paused:
      embed = Embed()
      embed.description = 'Mi hai liberato col tuo Frutto del Diavolo!!'
      await ctx.channel.send(embed=embed)
      await player.set_pause(False)
    elif player.is_playing:
      embed = Embed()
      embed.description = 'Mi hai fermato col tuo Frutto del Diavolo!!'
      await ctx.channel.send(embed=embed)
      await player.set_pause(True)

  @commands.command(name='leave')
  async def leave(self, ctx):
    embed = Embed()
    embed.description = 'Ok vado dal parruchiere ciao'
    player = self.bot.music.player_manager.get(ctx.guild.id)
    await ctx.channel.send(embed=embed)
    await self.connect_to(ctx.guild.id, None)
    if player.is_playing:
      await player.stop()


  async def track_hook(self, event):
    if isinstance(event, lavalink.events.QueueEndEvent):
      guild_id = int(event.player.guild_id)
      await self.connect_to(guild_id, None)
      
  async def connect_to(self, guild_id: int, channel_id: str):
    ws = self.bot._connection._get_websocket(guild_id)
    await ws.voice_state(str(guild_id), channel_id)

def setup(bot):
  bot.add_cog(MusicCog(bot))