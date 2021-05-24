from discord import ClientException
from discord.ext.commands import command, BadArgument

from utilidades import imprimir_evento


# ID_ROL = {
#     'administrador': 387344390030360587,
#     'colono': 493523298429435905,
#     'recluta': 493522659548856320,
#     'bot': 493784221085597706,
#     'everyone': 360868977754505217
# }


@command()

async def clear(ctx, arg):
    try:
        print(arg)
        cantidad = int(arg)

        if not ctx.author.guild_permissions.administrator or cantidad <= 0:
            raise BadArgument

        mensajes = await ctx.message.channel.history(limit=cantidad + 1).flatten()
        await ctx.message.channel.delete_messages(mensajes)

        if cantidad > 1:
            texto = 'clear: Se han borrado {} mensajes en "{}" ({})'
        else:
            texto = 'clear: Se ha borrado {} mensaje en "{}" ({})'
        imprimir_evento(texto, cantidad, ctx.channel, ctx.channel.category)

    except (ValueError, BadArgument):
        await ctx.message.delete()
    except ClientException:
        await ctx.send('El máximo es 100 primo')
