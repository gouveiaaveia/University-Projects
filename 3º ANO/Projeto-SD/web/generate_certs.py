import os
import subprocess
import sys


def load_server_ip():
    """Carrega o SERVER_IP do ficheiro .env na pasta search."""
    env_path = os.path.join(os.path.dirname(__file__), "..", "search", ".env")
    server_ip = "localhost"  # valor por defeito
    
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith("SERVER_IP="):
                    server_ip = line.split("=", 1)[1].strip()
                    break
    
    return server_ip


def generate_certificates():
    """Gera certificados SSL auto-assinados."""
    
    # Carregar IP do .env
    server_ip = load_server_ip()
    print(f"SERVER_IP carregado do .env: {server_ip}")
    
    # Diretório para certificados
    cert_dir = os.path.join(os.path.dirname(__file__), "certs")
    os.makedirs(cert_dir, exist_ok=True)
    
    cert_file = os.path.join(cert_dir, "cert.pem")
    key_file = os.path.join(cert_dir, "key.pem")
    
    # Verificar se já existem
    if os.path.exists(cert_file) and os.path.exists(key_file):
        print("Certificados já existem:")
        print(f"   - {cert_file}")
        print(f"   - {key_file}")
        
        response = input("\nDeseja regenerar os certificados? (s/N): ")
        if response.lower() != 's':
            print("Operação cancelada.")
            return
    
    print("\nA gerar certificados SSL auto-assinados...")
    print("   (Válidos por 365 dias)\n")
    
    # Configuração do certificado
    subject = f"/C=PT/ST=Portugal/L=Coimbra/O=Googol/OU=Dev/CN={server_ip}"
    
    # SANs (Subject Alternative Names) - inclui o IP do .env automaticamente
    sans = f"DNS:localhost,DNS:*.localhost,IP:127.0.0.1,IP:0.0.0.0,DNS:{server_ip}"
    
    # Se o server_ip parece ser um IP (e não hostname), adiciona como IP
    if server_ip not in ["localhost", "127.0.0.1", "0.0.0.0"]:
        # Verificar se é um IP válido
        parts = server_ip.split(".")
        if len(parts) == 4 and all(p.isdigit() for p in parts):
            sans += f",IP:{server_ip}"
            print(f"  IP {server_ip} adicionado aos SANs")
        else:
            sans += f",DNS:{server_ip}"
            print(f"  Hostname {server_ip} adicionado aos SANs")
    
    # Comando OpenSSL para gerar certificado auto-assinado
    cmd = [
        "openssl", "req",
        "-x509",                    # Certificado auto-assinado
        "-newkey", "rsa:4096",      # Nova chave RSA de 4096 bits
        "-keyout", key_file,         # Ficheiro da chave privada
        "-out", cert_file,           # Ficheiro do certificado
        "-days", "365",              # Validade de 365 dias
        "-nodes",                    # Sem password na chave
        "-subj", subject,            # Informação do certificado
        "-addext", f"subjectAltName={sans}"  # SANs
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Certificados gerados com sucesso!")
            print(f"\n   Certificado: {cert_file}")
            print(f"   Chave Privada: {key_file}")
            print("\nPara usar HTTPS:")
            print("   1. Execute: python app_mvc.py")
            print("   2. Aceda a: https://localhost:8000")
            print("\nNOTA: O browser mostrará um aviso porque o certificado")
            print("   é auto-assinado. Clique em 'Avançadas' > 'Continuar'")
        else:
            print("Erro ao gerar certificados:")
            print(result.stderr)
            
    except FileNotFoundError:
        print("OpenSSL não encontrado!")
        print("\nInstale o OpenSSL:")
        print("  - Ubuntu/Debian: sudo apt install openssl")
        print("  - macOS: brew install openssl")
        print("  - Windows: Descarregue de https://slproweb.com/products/Win32OpenSSL.html")
        sys.exit(1)


def verify_certificates():
    """Verifica e mostra informação dos certificados."""
    cert_dir = os.path.join(os.path.dirname(__file__), "certs")
    cert_file = os.path.join(cert_dir, "cert.pem")
    
    if not os.path.exists(cert_file):
        print("Certificado não encontrado. Execute sem argumentos para gerar.")
        return
    
    print("Informação do certificado:\n")
    
    cmd = ["openssl", "x509", "-in", cert_file, "-text", "-noout"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Extrair informação relevante
        lines = result.stdout.split('\n')
        for line in lines:
            if any(x in line for x in ['Subject:', 'Issuer:', 'Not Before', 'Not After', 'DNS:', 'IP Address']):
                print(line.strip())
                
    except Exception as e:
        print(f"Erro: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--verify":
        verify_certificates()
    else:
        generate_certificates()
