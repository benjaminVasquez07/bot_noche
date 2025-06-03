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
