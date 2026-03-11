import os
import sys
import ssl
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente da raiz do projeto
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / '.env')

# Adicionar diretórios ao path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
search_dir = os.path.join(current_dir, '../search')
sys.path.append(search_dir)

# FastAPI imports
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# Criar aplicação
app = FastAPI(
    title="Googol",
    description="Motor de Pesquisa Distribuído",
    version="2.0.0"
)

# Montar ficheiros estáticos
app.mount("/static", StaticFiles(directory=os.path.join(current_dir, "templates")), name="static")

# Importar e registar controllers
from controllers.home_controller import router as home_router
from controllers.search_controller import router as search_router
from controllers.index_controller import router as index_router
from controllers.stats_controller import router as stats_router
from controllers.ai_controller import router as ai_router
from controllers.api_controller import router as api_router

app.include_router(home_router)
app.include_router(search_router)
app.include_router(index_router)
app.include_router(stats_router)
app.include_router(ai_router)
app.include_router(api_router)


# ==========================================
#  ARRANQUE
# ==========================================

if __name__ == "__main__":
    import uvicorn
    
    # Verificar se existem certificados para HTTPS
    cert_dir = os.path.join(current_dir, "certs")
    cert_file = os.path.join(cert_dir, "cert.pem")
    key_file = os.path.join(cert_dir, "key.pem")
    
    use_https = os.path.exists(cert_file) and os.path.exists(key_file)
    
    if use_https:
        print("🔒 A iniciar Servidor Web FastAPI com HTTPS na porta 8000...")
        print(f"   Certificado: {cert_file}")
        print(f"   Chave: {key_file}")
        uvicorn.run(
            "app:app", 
            host="0.0.0.0", 
            port=8000, 
            reload=True,
            ssl_keyfile=key_file,
            ssl_certfile=cert_file
        )
    else:
        print("⚠️  Certificados HTTPS não encontrados em ./certs/")
        print("   Para ativar HTTPS, execute: python generate_certs.py")
        print("🌐 A iniciar Servidor Web FastAPI com HTTP na porta 8000...")
        uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
