import os
import json
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

# ----------------------------- FUNÇÕES -----------------------------
def carregar_fichas():
    try:
        with open("fichas.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def salvar_fichas(dados):
    with open("fichas.json", "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

# ----------------------------- COMANDOS -----------------------------
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
        await update.message.reply_text("❌ Personagem já existe.")
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
    await update.message.reply_text(f"✅ Personagem {nome} criado!")
    return ConversationHandler.END

# --- Funções de edição / submenu / salvar (igual versão anterior) ---
# ... (mesmo código das funções editar_ficha, escolher_personagem, escolher_campo, submenu_moedas, salvar_edicao, ver_ficha, mostrar_ficha, deletar_ficha, confirmar_delecao, status)
# Para simplificar não repeti aqui, mas você mantém o mesmo código que já funcionava

# ------------------- FLASK PARA UPTIME ROBOT -------------------
def start_flask():
    app_http = Flask("")
    @app_http.route("/")
    def home():
        return "Bot está online!"
    app_http.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))

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

    # --- Iniciar Flask em thread separada ---
    threading.Thread(target=start_flask, daemon=True).start()

    # --- Iniciar bot ---
    print("🤖 Bot rodando...")
    app.run_polling()

if __name__ == "__main__":
    main()
