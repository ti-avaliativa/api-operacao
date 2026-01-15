"""
Processador de arquivos CSV
"""
import csv
import io
import hashlib
from typing import List, Dict, Any

def detect_duplicates(data_list: List[Dict], key_fields: List[str]) -> Dict[str, List[int]]:
    """
    Detecta duplicatas baseado nos campos especificados
    Retorna dict com hash da linha como chave e lista de índices como valor
    """
    duplicates = {}
    seen = {}
    
    for idx, row in enumerate(data_list):
        # Cria hash dos campos chave
        key_values = tuple(str(row.get(field, "")).strip().upper() for field in key_fields)
        key_hash = hashlib.md5(str(key_values).encode()).hexdigest()
        
        if key_hash in seen:
            if key_hash not in duplicates:
                duplicates[key_hash] = [seen[key_hash], idx]
            else:
                duplicates[key_hash].append(idx)
        else:
            seen[key_hash] = idx
    
    return duplicates

def process_csv_data(file_content: str, required_fields: List[str]) -> Dict[str, Any]:
    """
    Processa dados do CSV e retorna dados validados e erros
    Aceita delimitadores: vírgula (,) ou ponto e vírgula (;)
    """
    errors = []
    valid_rows = []
    total_rows = 0

    try:
        # Remove BOM se existir
        if file_content.startswith('\ufeff'):
            file_content = file_content[1:]

        # Detecta delimitador (vírgula ou ponto e vírgula)
        sample = file_content[:1024]
        delimiter = ','

        try:
            sniffer = csv.Sniffer()
            detected = sniffer.sniff(sample, delimiters=',;')
            delimiter = detected.delimiter
        except:
            # Se falhar, tenta detectar manualmente
            if ';' in sample and sample.count(';') > sample.count(','):
                delimiter = ';'

        # Lê CSV
        csv_reader = csv.DictReader(io.StringIO(file_content), delimiter=delimiter)

        for row_idx, row in enumerate(csv_reader, start=2):  # Linha 2 porque 1 é header
            total_rows = row_idx - 1

            # Normaliza chaves do dicionário (remove espaços e converte para maiúsculas)
            normalized_row = {}
            for key, value in row.items():
                if key:  # Ignora chaves vazias
                    normalized_key = key.strip().upper()
                    normalized_row[normalized_key] = value

            # Verifica campos obrigatórios
            missing_fields = []
            for field in required_fields:
                if not normalized_row.get(field, "").strip():
                    missing_fields.append(field)

            if missing_fields:
                errors.append({
                    "linha": row_idx,
                    "erro": f"Campos obrigatórios vazios: {', '.join(missing_fields)}",
                    "dados": normalized_row
                })
                continue

            valid_rows.append({
                "linha_original": row_idx,
                "dados": normalized_row
            })

    except Exception as e:
        errors.append({
            "linha": 0,
            "erro": f"Erro ao processar CSV: {str(e)}",
            "dados": {}
        })

    return {
        "valid_rows": valid_rows,
        "errors": errors,
        "total_rows": total_rows
    }

def parse_csv_basic(file_content: str) -> Dict[str, Any]:
    """
    Parse básico de CSV retornando headers e linhas de dados
    Aceita delimitadores: vírgula (,) ou ponto e vírgula (;)
    """
    lines = [line.strip() for line in file_content.split('\n') if line.strip()]
    if len(lines) < 2:
        return {
            "success": False,
            "message": "O arquivo deve conter pelo menos uma linha de cabeçalho e uma linha de dados.",
            "headers": [],
            "data_rows": []
        }

    # Detecta delimitador (vírgula ou ponto e vírgula)
    first_line = lines[0]
    delimiter = ','
    if ';' in first_line and first_line.count(';') > first_line.count(','):
        delimiter = ';'

    headers = [h.strip().upper() for h in lines[0].split(delimiter)]
    data_rows = []

    for i, line in enumerate(lines[1:], 2):
        try:
            # Parser CSV básico
            values = []
            current = ""
            in_quotes = False

            for char in line:
                if char == '"':
                    in_quotes = not in_quotes
                elif char == delimiter and not in_quotes:
                    values.append(current.strip())
                    current = ""
                else:
                    current += char

            values.append(current.strip())

            # Ajusta número de colunas
            while len(values) < len(headers):
                values.append("")

            data_rows.append(values[:len(headers)])

        except Exception as e:
            continue  # Ignora linhas com erro de parsing

    return {
        "success": True,
        "headers": headers,
        "data_rows": data_rows,
        "total_rows": len(data_rows)
    }

