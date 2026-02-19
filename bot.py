import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

import os
TOKEN = os.getenv("TOKEN")

# Estados da conversa
ESCOLHER_PERSONAGEM, ESCOLHER_CAMPO, EDITANDO, NOME_JOGADOR, NOME_NOVA_FICHA, ESCOLHER_TIPO_MOEDA, EDITAR_MOEDA, INVENTARIO_SUBMENU = range(8)

# ------------------- Funções de dados -------------------
def carregar_fichas():
    try:
        with open("fichas.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def salvar_fichas(dados):
    with open("fichas.json", "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

# ------------------- Teclados -------------------
def teclado_campos():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Nome do Jogador", callback_data="campo_jogador")],
        [InlineKeyboardButton("Nome do personagem", callback_data="campo_nome")],
        [InlineKeyboardButton("Nível", callback_data="campo_nivel")],
        [InlineKeyboardButton("Rank", callback_data="campo_rank")],
        [InlineKeyboardButton("Raça", callback_data="campo_raca")],
        [InlineKeyboardButton("Classe", callback_data="campo_classe")],
        [InlineKeyboardButton("História", callback_data="campo_historia")],
        [InlineKeyboardButton("Desvantagem", callback_data="campo_desvantagem")],
        [InlineKeyboardButton("Antecedentes", callback_data="campo_antecedentes")],
        [InlineKeyboardButton("Inventário", callback_data="campo_inventario")],
        [InlineKeyboardButton("🔚 Encerrar edição", callback_data="encerrar")],
    ])

def teclado_inventario():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Equipamentos", callback_data="inv_equipamentos")],
        [InlineKeyboardButton("Moedas", callback_data="inv_moedas")],
        [InlineKeyboardButton("🔙 Voltar", callback_data="voltar_inventario")],
    ])

def teclado_moedas():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Cobre (pc)", callback_data="moeda_pc")],
        [InlineKeyboardButton("Prata (pp)", callback_data="moeda_pp")],
        [InlineKeyboardButton("Electro (pe)", callback_data="moeda_pe")],
        [InlineKeyboardButton("Ouro (po)", callback_data="moeda_po")],
        [InlineKeyboardButton("Platina (pl)", callback_data="moeda_pl")],
        [InlineKeyboardButton("Moedas do Destino (md)", callback_data="moeda_md")],
        [InlineKeyboardButton("🔙 Voltar", callback_data="voltar_moedas")],
    ])

# ------------------- CRIAR FICHA -------------------
async def criar_ficha_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📝 Qual é o nome do jogador/dono desta ficha?")
    return NOME_JOGADOR

async def receber_nome_jogador(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["novo_jogador"] = update.message.text.strip()
    await update.message.reply_text("📝 Qual será o nome do personagem?")
    return NOME_NOVA_FICHA

async def receber_nome_ficha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = "admin"
    nome_personagem = update.message.text.strip()
    jogador = context.user_data.get("novo_jogador", "Desconhecido")
    dados = carregar_fichas()
    if user_id not in dados:
        dados[user_id] = {}
    if nome_personagem in dados[user_id]:
        await update.message.reply_text("❌ Já existe um personagem com esse nome!")
        return ConversationHandler.END

    dados[user_id][nome_personagem] = {
        "jogador": jogador,
        "nome": nome_personagem,
        "nivel": "",
        "rank": "",
        "raca": "",
        "classe": "",
        "historia": "",
        "desvantagem": "",
        "antecedentes": "",
        "inventario": {"equipamentos": "", "moedas": {"pc":"0","pp":"0","pe":"0","po":"0","pl":"0","md":"0"}}
    }
    salvar_fichas(dados)
    await update.message.reply_text(f"✅ Ficha de '{nome_personagem}' criada com sucesso!")
    return ConversationHandler.END

# ------------------- EDITAR FICHA -------------------
async def editar_ficha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = "admin"
    dados = carregar_fichas()
    if user_id not in dados or not dados[user_id]:
        await update.message.reply_text("❌ Nenhuma ficha cadastrada.")
        return ConversationHandler.END
    keyboard = [[InlineKeyboardButton(nome, callback_data=f"personagem_{nome}")] for nome in dados[user_id]]
    await update.message.reply_text("🎭 Escolha o personagem para editar:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ESCOLHER_PERSONAGEM

async def escolher_personagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    personagem = query.data.replace("personagem_", "")
    context.user_data["personagem"] = personagem
    await query.edit_message_text(f"✏️ Editando {personagem}\n\nEscolha o campo:", reply_markup=teclado_campos())
    return ESCOLHER_CAMPO

async def escolher_campo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "encerrar":
        await query.edit_message_text("✅ Edição encerrada.")
        return ConversationHandler.END

    if query.data == "campo_inventario":
        await query.edit_message_text("📦 Inventário - escolha o subitem:", reply_markup=teclado_inventario())
        return INVENTARIO_SUBMENU

    campo = query.data.replace("campo_", "")
    context.user_data["campo"] = campo
    await query.edit_message_text(f"✏️ Envie o novo valor para {campo}:")
    return EDITANDO

async def inventario_submenu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "voltar_inventario":
        await query.edit_message_text(f"✏️ Editando {context.user_data['personagem']}\n\nEscolha o campo:", reply_markup=teclado_campos())
        return ESCOLHER_CAMPO
    if query.data == "inv_equipamentos":
        context.user_data["campo"] = "equipamentos"
        await query.edit_message_text("✏️ Envie os equipamentos:")
        return EDITANDO
    if query.data == "inv_moedas":
        await query.edit_message_text("💰 Escolha a moeda para editar:", reply_markup=teclado_moedas())
        return ESCOLHER_TIPO_MOEDA

async def escolher_tipo_moeda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "voltar_moedas":
        await query.edit_message_text("📦 Inventário - escolha o subitem:", reply_markup=teclado_inventario())
        return INVENTARIO_SUBMENU
    tipo = query.data.replace("moeda_", "")
    context.user_data["campo"] = tipo
    await query.edit_message_text(f"✏️ Envie a quantidade de {tipo.upper()}:")
    return EDITAR_MOEDA

async def salvar_edicao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = "admin"
    personagem = context.user_data["personagem"]
    campo = context.user_data["campo"]
    dados = carregar_fichas()
    if user_id not in dados: dados[user_id] = {}
    if personagem not in dados[user_id]: dados[user_id][personagem] = {}

    moedas_tipos = ["pc","pp","pe","po","pl","md"]
    if campo in moedas_tipos:
        dados[user_id][personagem]["inventario"]["moedas"][campo] = update.message.text
    elif campo == "equipamentos":
        dados[user_id][personagem]["inventario"]["equipamentos"] = update.message.text
    else:
        dados[user_id][personagem][campo] = update.message.text

    salvar_fichas(dados)
    await update.message.reply_text("✅ Campo atualizado!\n\nEscolha outro campo:", reply_markup=teclado_campos())
    return ESCOLHER_CAMPO

# ------------------- VER FICHA -------------------
async def ver_ficha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = "admin"
    dados = carregar_fichas()
    if user_id not in dados or not dados[user_id]:
        await update.message.reply_text("❌ Nenhuma ficha cadastrada.")
        return
    keyboard = [[InlineKeyboardButton(nome, callback_data=f"ver_{nome}")] for nome in dados[user_id]]
    await update.message.reply_text("👀 Clique no personagem para ver toda a ficha:", reply_markup=InlineKeyboardMarkup(keyboard))

async def mostrar_ficha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    personagem = query.data.replace("ver_", "").strip()
    user_id = "admin"
    dados = carregar_fichas()
    if user_id not in dados or personagem not in dados[user_id]:
        await query.edit_message_text("❌ Ficha não encontrada.")
        return
    f = dados[user_id][personagem]

    texto = f"👤 Jogador: {f.get('jogador','Desconhecido')}\n────────\n"
    texto += f"🎭 Personagem: {f.get('nome','')}\n────────\n"
    texto += f"Nível: {f.get('nivel','')}\nRank: {f.get('rank','')}\n────────\n"
    texto += f"Raça: {f.get('raca','')}\nClasse: {f.get('classe','')}\n────────\n"
    texto += f"História: {f.get('historia','')}\nDesvantagem: {f.get('desvantagem','')}\nAntecedentes: {f.get('antecedentes','')}\n────────\n"
    texto += "📦 Inventário:\n"
    texto += f"- Equipamentos: {f.get('inventario', {}).get('equipamentos','')}\n- Moedas:\n"
    moedas = f.get("inventario", {}).get("moedas", {})
    moedas_nomes = {"pc":"Cobre","pp":"Prata","pe":"Electro","po":"Ouro","pl":"Platina","md":"Moedas do Destino"}
    for chave, valor in moedas.items():
        nome_moeda = moedas_nomes.get(chave, chave.upper())
        texto += f"  • {nome_moeda} ({chave}): {valor}\n"

    await query.edit_message_text(texto)

# ------------------- DELETAR FICHA -------------------
async def deletar_ficha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = "admin"
    dados = carregar_fichas()
    if user_id not in dados or not dados[user_id]:
        await update.message.reply_text("❌ Nenhuma ficha cadastrada.")
        return
    keyboard = [[InlineKeyboardButton(nome, callback_data=f"del_{nome}")] for nome in dados[user_id]]
    await update.message.reply_text("⚠️ Clique no personagem que deseja deletar:", reply_markup=InlineKeyboardMarkup(keyboard))

async def confirmar_delecao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    personagem = query.data.replace("del_", "").strip()
    user_id = "admin"
    dados = carregar_fichas()
    if user_id in dados and personagem in dados[user_id]:
        del dados[user_id][personagem]
        salvar_fichas(dados)
        await query.edit_message_text(f"✅ Ficha '{personagem}' deletada com sucesso!")
    else:
        await query.edit_message_text("❌ Ficha não encontrada.")

# ------------------- STATUS -------------------
RANK_HIERARQUIA = ["Deus", "Lendario", "sss", "ss", "s", "A", "Bc", "d", "e"]

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = "admin"
    dados = carregar_fichas()
    if user_id not in dados or not dados[user_id]:
        await update.message.reply_text("❌ Nenhuma ficha cadastrada.")
        return

    personagens = list(dados[user_id].values())

    def rank_index(p):
        try:
            return RANK_HIERARQUIA.index(p.get("rank","e"))
        except ValueError:
            return len(RANK_HIERARQUIA)

    personagens.sort(key=lambda x: (rank_index(x), x.get("nome","")))

    texto = "📊 Status dos Personagens\n────────\n"
    moedas_nomes = {"pc":"Cobre","pp":"Prata","pe":"Electro","po":"Ouro","pl":"Platina","md":"Moedas do Destino"}

    for p in personagens:
        texto += f"🎭 {p.get('nome','')} | Rank: {p.get('rank','')}\n"
        moedas = p.get("inventario", {}).get("moedas", {})
        texto += "💰 Moedas: " + ", ".join(f"{moedas_nomes.get(k,k)}:{v}" for k,v in moedas.items()) + "\n────────\n"

    await update.message.reply_text(texto)

# ------------------- MAIN -------------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # ConversationHandler para criar ficha
    conv_criar = ConversationHandler(
        entry_points=[CommandHandler("novaficha", criar_ficha_start)],
        states={
            NOME_JOGADOR:[MessageHandler(filters.TEXT & ~filters.COMMAND, receber_nome_jogador)],
            NOME_NOVA_FICHA:[MessageHandler(filters.TEXT & ~filters.COMMAND, receber_nome_ficha)],
        },
        fallbacks=[]
    )

    # ConversationHandler para editar ficha
    conv_editar = ConversationHandler(
        entry_points=[CommandHandler("editarficha", editar_ficha)],
        states={
            ESCOLHER_PERSONAGEM:[CallbackQueryHandler(escolher_personagem)],
            ESCOLHER_CAMPO:[CallbackQueryHandler(escolher_campo)],
            INVENTARIO_SUBMENU:[CallbackQueryHandler(inventario_submenu)],
            ESCOLHER_TIPO_MOEDA:[CallbackQueryHandler(escolher_tipo_moeda)],
            EDITAR_MOEDA:[MessageHandler(filters.TEXT & ~filters.COMMAND, salvar_edicao)],
            EDITANDO:[MessageHandler(filters.TEXT & ~filters.COMMAND, salvar_edicao)],
        },
        fallbacks=[]
    )

    # Handlers gerais
    app.add_handler(conv_criar)
    app.add_handler(conv_editar)
    app.add_handler(CommandHandler("verficha", ver_ficha))
    app.add_handler(CallbackQueryHandler(mostrar_ficha, pattern=r"^ver_"))
    app.add_handler(CommandHandler("deletarficha", deletar_ficha))
    app.add_handler(CallbackQueryHandler(confirmar_delecao, pattern=r"^del_"))
    app.add_handler(CommandHandler("Status", status))  # <-- comando Status

    print("🤖 Bot rodando...")
    app.run_polling()

if __name__=="__main__":
    main()