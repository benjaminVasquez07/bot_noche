import discord
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
    print(f'Bot conectado como {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!mafia crear'):
        try:
            num = int(message.content.split()[2])
            if num < 3:
                return await message.channel.send("Mínimo 3 jugadores.")
            partidas[message.channel.id] = {
                "jugadores": [],
                "num": num,
                "mafiosos": [],
                "vivos": [],
                "fase": "lobby",
                "canal_mafiosos": None,
                "votos_mafiosos": set()
            }
            await message.channel.send(f"Partida creada para {num} jugadores. Usa `!mafia unirme`")
        except:
            await message.channel.send("Uso: !mafia crear <número>")

    elif message.content.startswith('!mafia unirme'):
        if message.channel.id in partidas:
            p = partidas[message.channel.id]
            if message.author.id not in p["jugadores"] and len(p["jugadores"]) < p["num"]:
                p["jugadores"].append(message.author.id)
                await message.channel.send(f"{message.author.mention} se ha unido ({len(p['jugadores'])}/{p['num']})")
                if len(p["jugadores"]) == p["num"]:
                    await asignar_roles(message.channel.id)
            elif message.author.id in p["jugadores"]:
                await message.channel.send("Ya estás en la partida.")
            else:
                await message.channel.send("La partida está llena.")
        else:
            await message.channel.send("No hay partida creada en este canal.")

    elif message.content.startswith('!mafia matar'):
        for partida_id, partida in partidas.items():
            if partida["canal_mafiosos"] and message.channel.id == partida["canal_mafiosos"].id:
                if partida["fase"] == "noche" and message.author.id in partida["mafiosos"]:
                    try:
                        objetivo = message.content.split()[2]
                        await matar(partida_id, message.author.id, objetivo)
                        partida["votos_mafiosos"].add(message.author.id)
                        if len(partida["votos_mafiosos"]) == len(partida["mafiosos"]):
                            await iniciar_dia(partida_id)
                        return
                    except IndexError:
                        await message.author.send("Uso: !mafia matar <nombre>")
                else:
                    await message.channel.send("Ahora no es la fase de noche o no estás en el canal de los mafiosos.")
                return
        await message.channel.send("No hay partida en curso.")

async def asignar_roles(channel_id):
    p = partidas[channel_id]
    jugadores = p["jugadores"][:]
    random.shuffle(jugadores)
    num_mafiosos = max(1, len(jugadores) // 3)

    p["mafiosos"] = jugadores[:num_mafiosos]
    p["vivos"] = jugadores[:]

    guild = client.get_channel(channel_id).guild
    category = await guild.create_category("Partida de Mafia")
    canal_mafiosos = await guild.create_text_channel("mafiosos-secretos", category=category)
    p["canal_mafiosos"] = canal_mafiosos

    await canal_mafiosos.set_permissions(guild.default_role, read_messages=False)
    for j in p["mafiosos"]:
        user = guild.get_member(j)
        await canal_mafiosos.set_permissions(user, read_messages=True, send_messages=True)

    for j in p["mafiosos"]:
        user = guild.get_member(j)
        otros = [guild.get_member(m).display_name for m in p["mafiosos"] if m != j]
        msg = "Tu rol: **MAFIOSO**. Usa `!mafia matar <nombre>` en la noche."
        if otros:
            msg += f"\nOtros mafiosos: {', '.join(otros)}"
        await user.send(msg)

    for j in jugadores[num_mafiosos:]:
        user = guild.get_member(j)
        await user.send("Tu rol: **CIUDADANO**. Sobrevive y encuentra a los mafiosos.")

    p["fase"] = "noche"
    await canal_mafiosos.send("🌙 **NOCHE** - Mafiosos usen `!mafia matar <nombre>`")
    await client.get_channel(channel_id).send("🌙 **NOCHE** - Los mafiosos están deliberando.")

async def iniciar_dia(partida_id):
    p = partidas[partida_id]
    p["fase"] = "dia"
    await client.get_channel(partida_id).send("☀️ **DÍA** - Ciudadanos discutan.")
    await asyncio.sleep(60)
    await iniciar_noche(partida_id)

async def iniciar_noche(partida_id):
    p = partidas[partida_id]
    p["fase"] = "noche"
    p["votos_mafiosos"] = set()
    await p["canal_mafiosos"].send("🌙 **NOCHE** - Mafiosos usen `!mafia matar <nombre>`")
    await client.get_channel(partida_id).send("🌙 **NOCHE** - Los mafiosos están deliberando.")

async def matar(partida_id, asesino_id, nombre):
    p = partidas[partida_id]
    objetivo_id = None

    for j in p["vivos"]:
        user = client.get_user(j)
        if user and user.display_name.lower() == nombre.lower():
            objetivo_id = j
            break

    if not objetivo_id:
        return await client.get_user(asesino_id).send("Jugador no encontrado.")

    p["vivos"].remove(objetivo_id)
    objetivo = client.get_user(objetivo_id)
    await client.get_user(asesino_id).send(f"Mataste a {objetivo.display_name}.")
    await client.get_channel(partida_id).send(f"💀 {objetivo.display_name} ha sido eliminado.")

client.run(TOKEN)