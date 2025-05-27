import discord  # type: ignore
import os
import random
import asyncio

# Cargar variables de entorno
TOKEN = os.getenv("DISCORD_TOKEN")

# Crear cliente
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Habilitar el intent de miembros del servidor
client = discord.Client(intents=intents)

# Roles del juego
roles = ["Mafioso", "Ciudadano", "Doctor", "Detective"]

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
            num_jugadores = int(message.content.split()[2])
            partidas[message.channel.id] = {
                "jugadores": [],
                "roles": roles,
                "creador": message.author.id,
                "num_jugadores": num_jugadores,
                "fase": "día",
                "votos": {},
                "victima": None,
                "protegido": None
            }
            await message.channel.send(f"Se ha creado una partida de Mafia para {num_jugadores} jugadores. Usa `!mafia unirme` para participar.")
        except (IndexError, ValueError):
            await message.channel.send("Uso: !mafia crear <número de jugadores>")

    elif message.content.startswith('!mafia unirme'):
        if message.channel.id in partidas:
            partida = partidas[message.channel.id]
            if len(partida["jugadores"]) < partida["num_jugadores"]:
                partida["jugadores"].append(message.author.id)
                await message.channel.send(f"{message.author.mention} se ha unido. Jugadores actuales: {len(partida['jugadores'])}/{partida['num_jugadores']}")

                if len(partida["jugadores"]) == partida["num_jugadores"]:
                    await asignar_roles(message.channel.id)
                    # Iniciar el ciclo de fases automáticamente
                    client.loop.create_task(ciclo_fases(message.channel.id))
            else:
                await message.channel.send("La partida ya está llena.")
        else:
            await message.channel.send("No hay una partida creada en este canal.")

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
                            partida["victima"] = victima
                            await message.channel.send(f"Los mafiosos han elegido a {victima.mention}. Se procesará al amanecer.")
                        else:
                            await message.channel.send("Jugador no encontrado.")
                    except IndexError:
                        await message.channel.send("Uso: !matar <nombre del jugador>")
                else:
                    await message.channel.send("Solo los mafiosos pueden usar este comando.")
            else:
                await message.channel.send("Ahora no es la fase de noche.")
        else:
            await message.channel.send("No hay una partida en curso en este canal.")

    elif message.content.startswith('!proteger'):
        if message.channel.id in partidas:
            partida = partidas[message.channel.id]
            if partida["fase"] == "noche":
                jugador = message.author
                rol = partida["roles"][partida["jugadores"].index(jugador.id)]

                if rol == "Doctor":
                    try:
                        protegido_nombre = message.content.split()[1]
                        protegido = discord.utils.get(message.channel.guild.members, name=protegido_nombre)
                        if protegido:
                            partida["protegido"] = protegido
                            await message.channel.send(f"El doctor ha elegido proteger a {protegido.mention} esta noche.")
                        else:
                            await message.channel.send("Jugador no encontrado.")
                    except IndexError:
                        await message.channel.send("Uso: !proteger <nombre del jugador>")
                else:
                    await message.channel.send("Solo el doctor puede usar este comando.")
            else:
                await message.channel.send("Ahora no es la fase de noche.")
        else:
            await message.channel.send("No hay una partida en curso en este canal.")

    elif message.content.startswith('!investigar'):
        if message.channel.id in partidas:
            partida = partidas[message.channel.id]
            if partida["fase"] == "noche":
                jugador = message.author
                rol = partida["roles"][partida["jugadores"].index(jugador.id)]

                if rol == "Detective":
                    try:
                        investigado_nombre = message.content.split()[1]
                        investigado = discord.utils.get(message.channel.guild.members, name=investigado_nombre)
                        if investigado:
                            rol_investigado = partida["roles"][partida["jugadores"].index(investigado.id)]
                            await message.channel.send(f"El detective ha investigado a {investigado.mention} y ha descubierto que es {rol_investigado}.")
                        else:
                            await message.channel.send("Jugador no encontrado.")
                    except IndexError:
                        await message.channel.send("Uso: !investigar <nombre del jugador>")
                else:
                    await message.channel.send("Solo el detective puede usar este comando.")
            else:
                await message.channel.send("Ahora no es la fase de noche.")
        else:
            await message.channel.send("No hay una partida en curso en este canal.")

    elif message.content.startswith('!votar'):
        if message.channel.id in partidas:
            partida = partidas[message.channel.id]
            if partida["fase"] == "día":
                try:
                    votado_nombre = message.content.split()[1]
                    votado = discord.utils.get(message.channel.guild.members, name=votado_nombre)
                    if votado:
                        if votado.id not in partida["votos"]:
                            partida["votos"][votado.id] = 0
                        partida["votos"][votado.id] += 1
                        await message.channel.send(f"{message.author.mention} ha votado para eliminar a {votado.mention}.")
                    else:
                        await message.channel.send("Jugador no encontrado.")
                except IndexError:
                    await message.channel.send("Uso: !votar <nombre del jugador>")
            else:
                await message.channel.send("Ahora no es la fase de día.")
        else:
            await message.channel.send("No hay una partida en curso en este canal.")

async def ciclo_fases(channel_id):
    partida = partidas[channel_id]
    while True:
        await asyncio.sleep(60)  # Esperar 60 segundos para cambiar de fase
        if partida["fase"] == "día":
            partida["fase"] = "noche"
            await client.get_channel(channel_id).send("Es de noche. Los mafiosos pueden elegir a quién eliminar en secreto usando `!matar <nombre>`, el doctor puede proteger a alguien con `!proteger <nombre>`, y el detective puede investigar a alguien con `!investigar <nombre>`. Envía estos comandos en privado al bot.")
        else:
            partida["fase"] = "día"
            if partida["victima"]:
                victima = partida["victima"]
                if partida["protegido"] == victima:
                    await client.get_channel(channel_id).send(f"¡Es de día! {victima.mention} fue protegido por el doctor y no fue eliminado.")
                else:
                    await client.get_channel(channel_id).send(f"¡Es de día! {victima.mention} ha sido eliminado por la mafia.")
                partida["victima"] = None
            else:
                await client.get_channel(channel_id).send("¡Es de día! No hubo eliminaciones durante la noche.")
            partida["protegido"] = None

async def asignar_roles(channel_id):
    partida = partidas[channel_id]
    # Asegurar al menos un mafioso
    if "Mafioso" not in partida["roles"]:
        partida["roles"].append("Mafioso")
    random.shuffle(partida["roles"])
    for i, jugador_id in enumerate(partida["jugadores"]):
        jugador = client.get_user(jugador_id)
        rol = partida["roles"][i % len(partida["roles"])]
        if rol == "Mafioso":
            await jugador.send("Tu rol es Mafioso. Durante la noche, usa `!matar <nombre>` para eliminar a alguien en secreto.")
        elif rol == "Doctor":
            await jugador.send("Tu rol es Doctor. Durante la noche, usa `!proteger <nombre>` para proteger a alguien.")
        elif rol == "Detective":
            await jugador.send("Tu rol es Detective. Durante la noche, usa `!investigar <nombre>` para descubrir el rol de alguien.")
        elif rol == "Ciudadano":
            await jugador.send("Tu rol es Ciudadano. No tienes habilidades especiales, pero puedes ayudar a descubrir a los mafiosos.")
    await client.get_channel(channel_id).send("Todos los roles han sido asignados. ¡Que comience el juego! Usa `!votar <nombre>` para votar durante el día.")

client.run(TOKEN)
