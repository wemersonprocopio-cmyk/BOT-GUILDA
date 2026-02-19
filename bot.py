import json
import os
import threading
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
from flask import Flask

# ----------------------------- CONSTANTES -----------------------------
ESCOLHER_PERSONAGEM, ESCOLHER_CAMPO, EDITANDO, SUBMENU_MOEDAS = range(4)

RANK_HIERARQUIA = ["Deus", "Lendario", "sss", "ss", "s", "A", "Bc", "d", "e"]
MOEDAS_NOMES = {"pc": "Cobre", "pp": "Prata", "pe": "Electro", "po": "Ouro", "pl": "Platina", "md": "Moedas do Destino"}

# ----------------------------- FUNÇÕES DE ARQUIVO -----------------------------
def carregar_fichas():
    try:
        with open("fichas.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def salvar_fichas(dados):
    with open("fichas.json", "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

# ----------------------------- COMANDOS BOT -----------------------------
async def criar_ficha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = "admin"
    dados = carregar_fichas()
    if user_id not in dados:
        dados[user_id] = {}

    await update.message.reply_text("✏️ Envie o nome do novo personagem:")
    return ESCOLHER_PERSONAGEM

async def receber_nome_personagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = "admin"
    nome = update.message.text.strip()
    dados = carregar_fichas()
    if nome in dados.get(user_id, {}):
        await update.message.reply_text("❌ Personagem já existe. Use outro nome.")
        return ConversationHandler.END

    dados[user_id][nome] = {
        "nome": nome,
        "jogador": user_id,
        "nivel": "",
        "rank": "",
        "raca": "",
        "classe": "",
        "historia": "",
        "desvantagem": "",
        "antecedentes": "",
        "inventario": {"equipamentos": [], "moedas": {"pc":0,"pp":0,"pe":0,"po":0,"pl":0,"md":0}}
    }
    salvar_fichas(dados)
    await update.message.reply_text(f"✅ Personagem {nome} criado com sucesso!")
    return ConversationHandler.END

# ------------------- EDITAR FICHA -------------------
async def editar_ficha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = "admin"
    dados = carregar_fichas()
    if user_id not in dados or not dados[user_id]:
        await update.message.reply_text("❌ Nenhum personagem cadastrado.")
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton(n, callback_data=f"personagem_{n}")] for n in dados[user_id]]
    await update.message.reply_text("🎭 Escolha o personagem:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ESCOLHER_PERSONAGEM

async def escolher_personagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    personagem = query.data.replace("personagem_", "")
    context.user_data["personagem"] = personagem

    keyboard = [
        [InlineKeyboardButton("Nome", callback_data="campo_nome")],
        [InlineKeyboardButton("Jogador", callback_data="campo_jogador")],
        [InlineKeyboardButton("Nivel", callback_data="campo_nivel")],
        [InlineKeyboardButton("Rank", callback_data="campo_rank")],
        [InlineKeyboardButton("Raça", callback_data="campo_raca")],
        [InlineKeyboardButton("Classe", callback_data="campo_classe")],
        [InlineKeyboardButton("História", callback_data="campo_historia")],
        [InlineKeyboardButton("Desvantagem", callback_data="campo_desvantagem")],
        [InlineKeyboardButton("Antecedentes", callback_data="campo_antecedentes")],
        [InlineKeyboardButton("Inventário", callback_data="campo_inventario")],
        [InlineKeyboardButton("🔚 Encerrar edição", callback_data="encerrar")]
    ]
    await query.edit_message_text(f"✏️ Editando {personagem}\nEscolha o campo:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ESCOLHER_CAMPO

async def escolher_campo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "encerrar":
        await query.edit_message_text("✅ Edição encerrada.")
        return ConversationHandler.END

    campo = query.data.replace("campo_", "")
    context.user_data["campo"] = campo

    if campo == "inventario":
        keyboard = [
            [InlineKeyboardButton("Equipamentos", callback_data="equipamentos")],
            [InlineKeyboardButton("Moedas", callback_data="moedas")],
            [InlineKeyboardButton("🔙 Voltar", callback_data="voltar")]
        ]
        await query.edit_message_text("📦 Escolha a sessão do inventário:", reply_markup=InlineKeyboardMarkup(keyboard))
        return SUBMENU_MOEDAS
    else:
        await query.edit_message_text(f"✏️ Envie o novo valor para {campo}:")
        return EDITANDO

async def submenu_moedas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    campo = query.data
    context.user_data["subcampo"] = campo
    if campo == "voltar":
        return await escolher_personagem(update, context)
    elif campo == "moedas":
        await query.edit_message_text("✏️ Envie o novo valor das moedas no formato: pc pp pe po pl md\nExemplo: 10 5 0 1 0 0")
        return EDITANDO
    else:  # equipamentos
        await query.edit_message_text("✏️ Envie os equipamentos separados por vírgula")
        return EDITANDO

async def salvar_edicao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = "admin"
    personagem = context.user_data["personagem"]
    campo = context.user_data["campo"]
    dados = carregar_fichas()

    if campo == "moedas" and "subcampo" in context.user_data:
        try:
            valores = list(map(int, update.message.text.strip().split()))
            if len(valores) != 6:
                raise ValueError
            dados[user_id][personagem]["inventario"]["moedas"] = dict(zip(MOEDAS_NOMES.keys(), valores))
        except:
            await update.message.reply_text("❌ Formato incorreto. Use: pc pp pe po pl md")
            return EDITANDO
    elif campo == "equipamentos" and "subcampo" in context.user_data:
        equipamentos = [e.strip() for e in update.message.text.strip().split(",")]
        dados[user_id][personagem]["inventario"]["equipamentos"] = equipamentos
    else:
        dados[user_id][personagem][campo] = update.message.text

    salvar_fichas(dados)
    await update.message.reply_text("✅ Campo atualizado!")
    return ConversationHandler.END

# ------------------- VER FICHA -------------------
async def ver_ficha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = "admin"
    dados = carregar_fichas()
    if user_id not in dados or not dados[user_id]:
        await update.message.reply_text("❌ Nenhum personagem cadastrado.")
        return
    keyboard = [[InlineKeyboardButton(n, callback_data=f"ver_{n}")] for n in dados[user_id]]
    await update.message.reply_text("🎭 Escolha o personagem para ver:", reply_markup=InlineKeyboardMarkup(keyboard))

async def mostrar_ficha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    nome = query.data.replace("ver_", "")
    dados = carregar_fichas()
    p = dados["admin"][nome]

    texto = f"──────────────\n🎭 {p.get('nome','')}\nJogador: {p.get('jogador','')}\nNível: {p.get('nivel','')}\nRank: {p.get('rank','')}\n──────────────\n"
    texto += f"Raça: {p.get('raca','')}\nClasse: {p.get('classe','')}\nHistória: {p.get('historia','')}\nDesvantagem: {p.get('desvantagem','')}\nAntecedentes: {p.get('antecedentes','')}\n──────────────\n"
    texto += "Inventário:\nEquipamentos: " + ", ".join(p.get("inventario", {}).get("equipamentos", [])) + "\n"
    moedas = p.get("inventario", {}).get("moedas", {})
    texto += "Moedas: " + ", ".join(f"{MOEDAS_NOMES.get(k,k)}:{v}" for k,v in moedas.items()) + "\n──────────────"
    await query.edit_message_text(texto)

# ------------------- DELETAR FICHA -------------------
async def deletar_ficha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = "admin"
    dados = carregar_fichas()
    if user_id not in dados or not dados[user_id]:
        await update.message.reply_text("❌ Nenhum personagem cadastrado.")
        return
    keyboard = [[InlineKeyboardButton(n, callback_data=f"del_{n}")] for n in dados[user_id]]
    await update.message.reply_text("⚠️ Escolha o personagem para deletar:", reply_markup=InlineKeyboardMarkup(keyboard))

async def confirmar_delecao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    nome = query.data.replace("del_", "")
    dados = carregar_fichas()
    del dados["admin"][nome]
    salvar_fichas(dados)
    await query.edit_message_text(f"✅ Personagem {nome} deletado!")

# ------------------- STATUS -------------------
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
        except:
            return len(RANK_HIERARQUIA)
    personagens.sort(key=lambda x: (rank_index(x), x.get("nome","")))
    texto = "📊 Status dos Personagens\n──────────────\n"
    for p in personagens:
        texto += f"🎭 {p.get('nome','')} | Rank: {p.get('rank','')}\n"
        moedas = p.get("inventario", {}).get("moedas", {})
        texto += "💰 Moedas: " + ", ".join(f"{MOEDAS_NOMES.get(k,k)}:{v}" for k,v in moedas.items()) + "\n──────────────\n"
    await update.message.reply_text(texto)

# ----------------------------- MAIN -----------------------------
def main():
    TOKEN = os.getenv("TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()

    # Conversas
    conv_criar = ConversationHandler(
        entry_points=[CommandHandler("criarficha", criar_ficha)],
        states={ESCOLHER_PERSONAGEM:[MessageHandler(filters.TEXT & ~filters.COMMAND, receber_nome_personagem)]},
        fallbacks=[]
    )
    conv_editar = ConversationHandler(
        entry_points=[CommandHandler("editarficha", editar_ficha)],
        states={
            ESCOLHER_PERSONAGEM: [CallbackQueryHandler(escolher_personagem)],
            ESCOLHER_CAMPO: [CallbackQueryHandler(escolher_campo)],
            SUBMENU_MOEDAS: [CallbackQueryHandler(submenu_moedas)],
            EDITANDO: [MessageHandler(filters.TEXT & ~filters.COMMAND, salvar_edicao)],
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
    app.add_handler(CommandHandler("status", status))

    print("🤖 Bot rodando...")
    app.run_polling()

# ------------------- FLASK PARA UPTIME ROBOT -------------------
app_http = Flask("")

@app_http.route("/")
def home():
    return "Bot está online!"

threading.Thread(target=lambda: app_http.run(host="0.0.0.0", port=8000)).start()

# ------------------- INICIAR BOT -------------------
if __name__ == "__main__":
    main()
