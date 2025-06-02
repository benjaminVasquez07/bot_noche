import discord  # type: ignore
import os
import random
import asyncio

TOKEN = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.default()
intents.message_content = True
intents.members = True 
client = discord.Client(intents=intents)
partidas = {}

@client.event
async def on_ready():
    print(f'|* Bot conectado como {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if message.content.startswith('!mafia crear'):
        try:
            num = int(message.content.split()[2])
            if num < 3: return await message.channel.send("Mínimo 3 jugadores.")
            partidas[message.channel.id] = {"jugadores": [], "num": num, "mafiosos": [], "vivos": [], "fase": "lobby"}
            await message.channel.send(f"Partida creada para {num} jugadores. Usa `!mafia unirme`")
        except: await message.channel.send("Uso: !mafia crear <número>")
    
    elif message.content.startswith('!mafia unirme'):
        if message.channel.id in partidas:
            p = partidas[message.channel.id]
            if message.author.id not in p["jugadores"] and len(p["jugadores"]) < p["num"]:
                p["jugadores"].append(message.author.id)
                await message.channel.send(f"{message.author.mention} unido ({len(p['jugadores'])}/{p['num']})")
                if len(p["jugadores"]) == p["num"]:
                    await asignar_roles(message.channel.id)
            else: await message.channel.send("Ya estás o partida llena.")
        else: await message.channel.send("No hay partida.")
    
    elif message.content.startswith('!matar'):
        if message.channel.id in partidas:
            p = partidas[message.channel.id]
            if p["fase"] == "noche" and message.author.id in p["mafiosos"]:
                try:
                    objetivo = message.content.split()[1]
                    await matar(message.channel.id, message.author.id, objetivo)
                except: await message.author.send("Uso: !matar <nombre>")

async def asignar_roles(channel_id):
    p = partidas[channel_id]
    jugadores = p["jugadores"][:]
    random.shuffle(jugadores)
    num_mafiosos = max(1, len(jugadores) // 3)
    
    p["mafiosos"] = jugadores[:num_mafiosos]
    p["vivos"] = jugadores[:]
    
    for j in p["mafiosos"]:
        user = client.get_user(j)
        otros = [client.get_user(m).display_name for m in p["mafiosos"] if m != j]
        msg = "Tu rol: **MAFIOSO**. Usa `!matar <nombre>` en la noche."
        if otros: msg += f"\nOtros mafiosos: {', '.join(otros)}"
        await user.send(msg)
    
    for j in jugadores[num_mafiosos:]:
        await client.get_user(j).send("Tu rol: **CIUDADANO**. Sobrevive y encuentra mafiosos.")
    
    await client.get_channel(channel_id).send("Roles asignados. ¡Empezamos!")
    await iniciar_noche(channel_id)

async def iniciar_noche(channel_id):
    if channel_id not in partidas: return
    p = partidas[channel_id]
    p["fase"] = "noche"
    await client.get_channel(channel_id).send("🌙 **NOCHE** - Mafiosos usen `!matar <nombre>`")
    await asyncio.sleep(30)
    await iniciar_dia(channel_id)

async def iniciar_dia(channel_id):
    if channel_id not in partidas: return
    p = partidas[channel_id]
    p["fase"] = "dia"
    await client.get_channel(channel_id).send("☀️ **DÍA** - Ciudadanos discutan")
    if await verificar_victoria(channel_id): return
    await asyncio.sleep(60)
    await iniciar_noche(channel_id)

async def matar(channel_id, asesino_id, nombre):
    p = partidas[channel_id]
    objetivo_id = None
    
    for j in p["vivos"]:
        if client.get_user(j).display_name.lower() == nombre.lower():
            objetivo_id = j
            break
    
    if not objetivo_id:
        return await client.get_user(asesino_id).send("Jugador no encontrado.")
    if objetivo_id in p["mafiosos"]:
        return await client.get_user(asesino_id).send("No puedes matar mafiosos.")
    
    p["vivos"].remove(objetivo_id)
    objetivo = client.get_user(objetivo_id)
    await client.get_user(asesino_id).send(f"Mataste a {objetivo.display_name}")
    await client.get_channel(channel_id).send(f"💀 {objetivo.display_name} murió.")

async def verificar_victoria(channel_id):
    p = partidas[channel_id]
    mafiosos_vivos = [m for m in p["mafiosos"] if m in p["vivos"]]
    ciudadanos_vivos = len(p["vivos"]) - len(mafiosos_vivos)
    
    if len(mafiosos_vivos) == 0:
        await client.get_channel(channel_id).send("🎉 **CIUDADANOS GANAN!**")
        del partidas[channel_id]
        return True
    elif len(mafiosos_vivos) >= ciudadanos_vivos:
        await client.get_channel(channel_id).send("🎉 **MAFIOSOS GANAN!**")
        del partidas[channel_id]
        return True
    return False

client.run(TOKEN)