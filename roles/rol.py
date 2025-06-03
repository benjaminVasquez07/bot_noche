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
