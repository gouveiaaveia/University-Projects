"""
Service de IA - Lógica de negócio para funcionalidades de IA.
Prioridade: 1) Groq, 2) Google Gemini, 3) Ollama local
"""
import requests
import json
import os
from typing import Generator, List, Dict, Optional


class AIService:
    """Service responsável por operações de IA."""
    
    def __init__(self):
        """
        Inicializa o service de IA.
        Prioridade: 1) Groq, 2) Google Gemini, 3) Ollama local
        """
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        
        # Configurar modelos
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "gemma3:1b")
        
        # URLs das APIs
        self.groq_api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.gemini_api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}"
        self.ollama_api_url = "http://localhost:11434/api/generate"
        
        # Determinar provider principal disponível
        self._detect_provider()
    
    def _detect_provider(self):
        """Deteta qual provider usar baseado nas chaves disponíveis."""
        if self.groq_api_key:
            self.provider = "groq"
            print(f"[AIService] Provider principal: Groq ({self.groq_model})")
        elif self.gemini_api_key:
            self.provider = "gemini"
            print(f"[AIService] Provider principal: Google Gemini ({self.gemini_model})")
        else:
            self.provider = "ollama"
            print(f"[AIService] Provider principal: Ollama local ({self.ollama_model})")
        
        # Log de fallbacks disponíveis
        fallbacks = []
        if self.groq_api_key and self.provider != "groq":
            fallbacks.append("Groq")
        if self.gemini_api_key and self.provider != "gemini":
            fallbacks.append("Gemini")
        fallbacks.append("Ollama")
        print(f"[AIService] Fallbacks disponíveis: {', '.join(fallbacks)}")
    
    # ==========================================
    #  GROQ API (Principal)
    # ==========================================
    
    def _groq_stream_response(self, messages: List[Dict], temperature: float = 0.7) -> Generator[str, None, None]:
        """Gera resposta em stream usando Groq."""
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.groq_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 2048,
            "stream": True
        }
        
        try:
            with requests.post(self.groq_api_url, headers=headers, json=payload, stream=True, timeout=120) as response:
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if line:
                        line_text = line.decode('utf-8')
                        if line_text.startswith("data: "):
                            data = line_text[6:]
                            if data.strip() == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                                choices = chunk.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    text = delta.get("content", "")
                                    if text:
                                        yield text
                            except json.JSONDecodeError:
                                continue
                                
        except requests.exceptions.ConnectionError:
            raise Exception("Não foi possível conectar à API do Groq")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"Erro HTTP Groq: {e}")
        except Exception as e:
            raise Exception(f"Erro Groq: {str(e)}")
    
    def _groq_complete(self, messages: List[Dict], temperature: float = 0.7) -> str:
        """Gera resposta completa (sem stream) usando Groq."""
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.groq_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 1024
        }
        
        try:
            response = requests.post(self.groq_api_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")
            return ""
            
        except Exception as e:
            raise Exception(f"Erro Groq: {str(e)}")

    # ==========================================
    #  GOOGLE GEMINI API
    # ==========================================
    
    def _gemini_stream_response(self, contents: List[Dict], temperature: float = 0.7) -> Generator[str, None, None]:
        """Gera resposta em stream usando Gemini."""
        url = f"{self.gemini_api_url}:streamGenerateContent?alt=sse&key={self.gemini_api_key}"
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 2048
            }
        }
        
        try:
            with requests.post(url, json=payload, stream=True, timeout=120) as response:
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if line:
                        line_text = line.decode('utf-8')
                        if line_text.startswith("data: "):
                            data = line_text[6:]
                            try:
                                chunk = json.loads(data)
                                candidates = chunk.get("candidates", [])
                                if candidates:
                                    content = candidates[0].get("content", {})
                                    parts = content.get("parts", [])
                                    if parts:
                                        text = parts[0].get("text", "")
                                        if text:
                                            yield text
                            except json.JSONDecodeError:
                                continue
                                
        except requests.exceptions.ConnectionError:
            raise Exception("Não foi possível conectar à API do Google Gemini")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"Erro HTTP Gemini: {e}")
        except Exception as e:
            raise Exception(f"Erro Gemini: {str(e)}")
    
    def _gemini_complete(self, contents: List[Dict], temperature: float = 0.7) -> str:
        """Gera resposta completa (sem stream) usando Gemini."""
        url = f"{self.gemini_api_url}:generateContent?key={self.gemini_api_key}"
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 1024
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            candidates = data.get("candidates", [])
            if candidates:
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if parts:
                    return parts[0].get("text", "")
            return ""
            
        except Exception as e:
            raise Exception(f"Erro Gemini: {str(e)}")
    
    # ==========================================
    #  OLLAMA LOCAL
    # ==========================================
    
    def _ollama_stream_response(self, prompt: str) -> Generator[str, None, None]:
        """Gera resposta em stream usando Ollama local."""
        try:
            response = requests.post(
                self.ollama_api_url,
                json={"model": self.ollama_model, "prompt": prompt, "stream": True},
                stream=True,
                timeout=120
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode('utf-8'))
                        text = data.get('response', '')
                        if text:
                            yield text
                    except json.JSONDecodeError:
                        continue
                        
        except requests.exceptions.ConnectionError:
            raise Exception("Ollama não está a correr. Executa 'ollama serve' primeiro.")
        except Exception as e:
            raise Exception(f"Erro Ollama: {str(e)}")
    
    def _ollama_complete(self, prompt: str, temperature: float = 0.7) -> str:
        """Gera resposta completa usando Ollama local."""
        try:
            response = requests.post(
                self.ollama_api_url,
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": temperature}
                },
                timeout=60
            )
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            raise Exception(f"Erro Ollama: {str(e)}")
    
    # ==========================================
    #  MÉTODOS PÚBLICOS (com Fallback)
    # ==========================================
    
    def _convert_to_groq_messages(self, question: str, history: List[Dict] = None) -> List[Dict]:
        """Converte para formato de mensagens Groq/OpenAI."""
        messages = [{"role": "system", "content": "Tu és um assistente inteligente chamado Googol IA. Responde sempre em Português de Portugal de forma clara, útil e amigável."}]
        
        if history:
            for msg in history[-10:]:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
        
        messages.append({"role": "user", "content": question})
        return messages
    
    def _convert_to_gemini_contents(self, question: str, history: List[Dict] = None) -> List[Dict]:
        """Converte para formato de conteúdos Gemini."""
        contents = []
        
        if history:
            for msg in history[-10:]:
                role = "user" if msg.get("role") == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg.get("content", "")}]
                })
        
        contents.append({
            "role": "user",
            "parts": [{"text": question}]
        })
        return contents
    
    def _convert_to_ollama_prompt(self, question: str, history: List[Dict] = None) -> str:
        """Converte para prompt Ollama."""
        system_prompt = "Tu és um assistente inteligente chamado Googol IA. Responde sempre em Português de Portugal de forma clara, útil e amigável."
        
        context = ""
        if history:
            context = "\n".join([
                f"{msg['role']}: {msg['content']}" 
                for msg in history[-5:]
            ])
            context += "\n"
        
        return f"{system_prompt}\n\n{context}user: {question}\nassistant:"
    
    def stream_answer(self, question: str) -> Generator[str, None, None]:
        """Gera resposta em stream para uma pergunta com fallback automático."""
        providers_to_try = self._get_provider_order()
        last_error = None
        
        for provider in providers_to_try:
            try:
                print(f"[AIService] A tentar provider: {provider}")
                
                if provider == "groq" and self.groq_api_key:
                    messages = self._convert_to_groq_messages(question)
                    yield from self._groq_stream_response(messages)
                    return
                    
                elif provider == "gemini" and self.gemini_api_key:
                    contents = self._convert_to_gemini_contents(question)
                    yield from self._gemini_stream_response(contents)
                    return
                    
                elif provider == "ollama":
                    prompt = self._convert_to_ollama_prompt(question)
                    yield from self._ollama_stream_response(prompt)
                    return
                    
            except Exception as e:
                last_error = str(e)
                print(f"[AIService] Falha no provider {provider}: {last_error}")
                continue
        
        yield f"Erro: Todos os providers de IA falharam. Último erro: {last_error}"
    
    def stream_chat_with_history(self, message: str, history: List[Dict]) -> Generator[str, None, None]:
        """Gera resposta em stream com histórico de conversa e fallback automático."""
        providers_to_try = self._get_provider_order()
        last_error = None
        
        for provider in providers_to_try:
            try:
                print(f"[AIService] Chat - A tentar provider: {provider}")
                
                if provider == "groq" and self.groq_api_key:
                    messages = self._convert_to_groq_messages(message, history)
                    yield from self._groq_stream_response(messages)
                    return
                    
                elif provider == "gemini" and self.gemini_api_key:
                    contents = self._convert_to_gemini_contents(message, history)
                    yield from self._gemini_stream_response(contents)
                    return
                    
                elif provider == "ollama":
                    prompt = self._convert_to_ollama_prompt(message, history)
                    yield from self._ollama_stream_response(prompt)
                    return
                    
            except Exception as e:
                last_error = str(e)
                print(f"[AIService] Chat - Falha no provider {provider}: {last_error}")
                continue
        
        yield f"Erro: Todos os providers de IA falharam. Último erro: {last_error}"
    
    def generate_search_summary(self, query: str, results: List[Dict]) -> str:
        """Gera resumo para resultados de pesquisa com fallback automático."""
        prompt_base = """Assuma o papel de um motor de pesquisa simplificado. 
A tua tarefa é gerar uma resposta curta (2-3 frases) e direta à pesquisa do utilizador.
Responde em português de forma clara e concisa.

Pesquisa do Utilizador: """
        
        full_prompt = f"{prompt_base}{query}"
        providers_to_try = self._get_provider_order()
        last_error = None
        
        for provider in providers_to_try:
            try:
                print(f"[AIService] Summary - A tentar provider: {provider}")
                
                if provider == "groq" and self.groq_api_key:
                    messages = [
                        {"role": "system", "content": "Tu és um assistente de pesquisa. Responde de forma concisa em Português de Portugal."},
                        {"role": "user", "content": full_prompt}
                    ]
                    return self._groq_complete(messages, temperature=0.5)
                    
                elif provider == "gemini" and self.gemini_api_key:
                    contents = [{"parts": [{"text": full_prompt}]}]
                    return self._gemini_complete(contents, temperature=0.5)
                    
                elif provider == "ollama":
                    return self._ollama_complete(full_prompt, temperature=0.5)
                    
            except Exception as e:
                last_error = str(e)
                print(f"[AIService] Summary - Falha no provider {provider}: {last_error}")
                continue
        
        return f"Erro ao gerar resumo: {last_error}"
    
    def _get_provider_order(self) -> List[str]:
        """Retorna a ordem de providers a tentar (principal primeiro, depois fallbacks)."""
        # Ordem fixa: Groq -> Gemini -> Ollama
        order = []
        if self.groq_api_key:
            order.append("groq")
        if self.gemini_api_key:
            order.append("gemini")
        order.append("ollama")
        return order
