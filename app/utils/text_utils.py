"""
Utilitários para manipulação de texto
"""
import html
import re
import unicodedata

def ai(STR):
    """Sanitiza string para prevenir injeção"""
    STR = html.escape(STR)
    STR = STR.replace(";", "")
    return str(STR)

def has_special_characters(text: str) -> bool:
    """
    Verifica se o texto contém caracteres especiais inválidos
    Permitido: letras (A-Z, a-z, com acentos), números (0-9), espaços
    Não permitido: @#$%&*()[]{}|\/~^`etc
    """
    if not text or not isinstance(text, str):
        return False

    # Verifica se contém apenas letras (incluindo acentuadas), números e espaços
    pattern = r'^[A-Za-z0-9\sÀ-ÿ]+$'

    # Se NÃO der match, significa que tem caracteres especiais
    has_invalid = not bool(re.match(pattern, text))

    if has_invalid:
        print(f"⚠️ Caracteres especiais detectados em: '{text}'")

    return has_invalid

def normalize_text(text: str) -> str:
    """
    Normaliza texto:
    - Trim (remove espaços início/fim)
    - Converte para MAIÚSCULO
    - Remove espaços extras (múltiplos espaços viram um)
    - Remove acentos
    """
    if not text or not isinstance(text, str):
        return ""

    # 1. Trim - remove espaços do início e fim
    text = text.strip()

    # 2. Converte para maiúsculo
    text = text.upper()

    # 3. Remove espaços extras (múltiplos espaços viram um)
    text = ' '.join(text.split())

    # 4. Remove acentos
    text = unicodedata.normalize('NFD', text)
    text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')

    # 5. Remove caracteres especiais, mantém apenas letras, números e espaços
    text = re.sub(r'[^A-Z0-9\s]', '', text)

    return text.strip()

def validate_email(email: str) -> dict:
    """
    Valida email
    Retorna: {"valid": bool, "email": str, "error": str}

    Regras:
    - Formato válido: xxx@xxx.xxx
    - Permite minúsculas (não converte para maiúsculas)
    - Faz trim (remove espaços)
    - Permite caracteres especiais no email (@, ., -, _)
    """
    if not email or not isinstance(email, str):
        return {"valid": True, "email": "", "error": ""}

    # Trim - remove espaços
    email = email.strip()

    # Se vazio após trim, retorna válido (campo opcional)
    if not email:
        return {"valid": True, "email": "", "error": ""}

    # Regex para validar email
    # Permite: letras, números, ., -, _ antes do @
    # Obrigatório: @ no meio
    # Permite: letras, números, ., - depois do @
    # Obrigatório: . seguido de 2-6 letras no final
    email_pattern = r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$'

    if not re.match(email_pattern, email):
        return {
            "valid": False,
            "email": email,
            "error": f"Email inválido: '{email}'"
        }

    return {"valid": True, "email": email, "error": ""}

def validate_phone(phone: str) -> str:
    """Valida e formata telefone"""
    if not phone:
        return ""
    # Remove tudo que não for número
    phone = re.sub(r'[^0-9]', '', phone)
    # Limita a 15 caracteres
    return phone[:15] if phone else ""

def calculate_similarity(str1: str, str2: str) -> float:
    """
    Calcula similaridade entre duas strings usando algoritmo de distância de Levenshtein
    Retorna valor entre 0 (nenhuma similaridade) e 1 (idênticas)
    """
    if not str1 or not str2:
        return 0.0
    
    str1, str2 = str1.lower(), str2.lower()
    if str1 == str2:
        return 1.0
    
    # Algoritmo básico de similaridade
    len1, len2 = len(str1), len(str2)
    if len1 == 0 or len2 == 0:
        return 0.0
    
    # Matriz para distância de Levenshtein
    matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]
    
    for i in range(len1 + 1):
        matrix[i][0] = i
    for j in range(len2 + 1):
        matrix[0][j] = j
    
    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if str1[i-1] == str2[j-1] else 1
            matrix[i][j] = min(
                matrix[i-1][j] + 1,      # deletion
                matrix[i][j-1] + 1,      # insertion
                matrix[i-1][j-1] + cost  # substitution
            )
    
    distance = matrix[len1][len2]
    max_len = max(len1, len2)
    return 1 - (distance / max_len)

def detect_similar_names(new_name: str, existing_names: list, threshold: float = 0.7) -> list:
    """
    Detecta nomes similares baseado em threshold de similaridade
    REGRA: Detecta apenas entre threshold e 99% (exclui 100% pois é duplicata exata)
    """
    similar = []
    for existing in existing_names:
        similarity = calculate_similarity(new_name, existing["nome"])
        # Detecta apenas entre threshold (70%) e 99% (exclui 100% = duplicata exata)
        if threshold <= similarity < 1.0:
            similar.append({
                "nome_existente": existing["nome"],
                "id_existente": existing.get("id"),
                "similaridade": round(similarity, 3)
            })

    return similar

