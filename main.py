import discord
import os
import random
import asyncio

# Cargar variables de entorno

TOKEN = os.getenv("DISCORD_TOKEN")

# Crear cliente
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)

# Roles del juego
roles = ["Mafioso", "Ciudadano"]

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
            num_jugadores = int(message.content.split()[2])
            partidas[message.channel.id] = {"jugadores": [], "roles": roles, "fase": "día"}
            await message.channel.send(f"Partida creada para {num_jugadores} jugadores. Usa `!mafia unirme`.")
        except (IndexError, ValueError):
            await message.channel.send("Uso: !mafia crear <número de jugadores>")

    elif message.content.startswith('!mafia unirme'):
        if message.channel.id in partidas:
            partida = partidas[message.channel.id]
            if len(partida["jugadores"]) < 10:  # Límite de jugadores
                partida["jugadores"].append(message.author.id)
                await message.author.send(f"Te has unido. Jugadores: {len(partida['jugadores'])}")
                if len(partida["jugadores"]) == 2:
                    await asignar_roles(message.channel.id)
                    client.loop.create_task(ciclo_fases(message.channel.id))
            else:
                await message.channel.send("La partida está llena.")
        else:
            await message.channel.send("No hay partida creada.")

    elif message.content.startswith('!matar'):
        if message.channel.id in partidas:
            partida = partidas[message.channel.id]
            if partida["fase"] == "noche":
                jugador = message.author
                rol = partida["roles"][partida["jugadores"].index(jugador.id)]
                if rol == "Mafioso":
                    try:
                        victima_nombre = message.content.split()[1]
                        victima = discord.utils.get(message.channel.guild.members, name=victima_nombre)
                        if victima:
                            await message.channel.send(f"Los mafiosos han elegido a {victima.mention}.")
                    except IndexError:
                        await message.channel.send("Uso: !matar <nombre del jugador>")
            else:
                await message.channel.send("Ahora no es la fase de noche.")
        else:
            await message.channel.send("No hay partida en curso.")

async def asignar_roles(channel_id):
    partida = partidas[channel_id]
    random.shuffle(partida["roles"])
    for i, jugador_id in enumerate(partida["jugadores"]):
        jugador = client.get_user(jugador_id)
        rol = partida["roles"][i % len(partida["roles"])]
        await jugador.send(f"Tu rol es {rol}.")

async def ciclo_fases(channel_id):
    partida = partidas[channel_id]
    while True:
        await asyncio.sleep(30)
        if partida["fase"] == "día":
            partida["fase"] = "noche"
            await client.get_channel(channel_id).send("Es de noche. Los mafiosos pueden usar `!matar <nombre>`.")
        else:
            partida["fase"] = "día"
            await client.get_channel(channel_id).send("¡Es de día!")

client.run(TOKEN)
