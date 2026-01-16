"""
Serviço de importação de estrutura (Escola, Série, Turma)
Responsabilidade: Lógica de negócio para importação de estrutura educacional
"""
from typing import Dict, Any, List
from app.core.database import get_db_connection
from app.utils.text_utils import normalize_text, has_special_characters, detect_similar_names
from app.utils.csv_processor import process_csv_data, detect_duplicates


class EstruturaService:
    """Serviço para gerenciar importação de estrutura educacional"""
    
    @staticmethod
    def validar_estrutura_csv(file_content: str, db_name: str = None, dry_run: bool = True) -> Dict[str, Any]:
        """
        Valida dados de estrutura do CSV

        Args:
            file_content: Conteúdo do arquivo CSV
            db_name: Nome do banco de dados a usar
            dry_run: Se True, apenas valida sem importar

        Returns:
            Dict com resultados da validação
        """
        # Processa CSV com campos obrigatórios
        result = process_csv_data(file_content, ["ESCOLA", "SERIE", "TURMA"])
        
        if not result["valid_rows"]:
            return {
                "success": False,
                "message": "Nenhuma linha válida encontrada",
                "errors": result["errors"],
                "stats": {
                    "total_linhas": result["total_rows"],
                    "escolas_criadas": 0,
                    "series_criadas": 0,
                    "turmas_criadas": 0,
                    "erros": len(result["errors"])
                }
            }
        
        # Detecta duplicatas (combinação escola+serie+turma)
        duplicates = detect_duplicates(
            [row["dados"] for row in result["valid_rows"]],
            ["ESCOLA", "SERIE", "TURMA"]
        )
        
        # Contadores
        escolas_criadas = 0
        series_criadas = 0
        turmas_criadas = 0
        validation_errors = []
        validation_warnings = []
        similar_schools = []  # Lista para armazenar escolas similares

        # Cache para evitar consultas repetidas
        escolas_cache = {}  # nome -> id
        series_cache = {}   # nome -> id

        # Criar set para rastrear combinações já processadas
        processed_combinations = set()
        escolas_unicas = set()
        series_unicas = set()

        # Lista para detectar nomes similares de escolas
        escolas_processadas = []

        with get_db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(f"USE {db_name}")
            
            for row_data in result["valid_rows"]:
                linha = row_data["linha_original"]
                dados = row_data["dados"]
                
                # Dados originais (SEM strip para detectar espaços)
                escola_raw = str(dados.get("ESCOLA", ""))
                serie_raw = str(dados.get("SERIE", ""))
                turma_raw = str(dados.get("TURMA", ""))

                # Validar espaços no início/fim
                if escola_raw != escola_raw.strip():
                    validation_warnings.append({
                        "linha": linha,
                        "aviso": f"Nome da escola contém espaços no início ou fim: '{escola_raw}'",
                        "dados": dados,
                        "tipo": "espacos_extras"
                    })

                if serie_raw != serie_raw.strip():
                    validation_warnings.append({
                        "linha": linha,
                        "aviso": f"Nome da série contém espaços no início ou fim: '{serie_raw}'",
                        "dados": dados,
                        "tipo": "espacos_extras"
                    })

                if turma_raw != turma_raw.strip():
                    validation_warnings.append({
                        "linha": linha,
                        "aviso": f"Nome da turma contém espaços no início ou fim: '{turma_raw}'",
                        "dados": dados,
                        "tipo": "espacos_extras"
                    })

                # Agora fazer strip
                escola_original = escola_raw.strip()
                serie_original = serie_raw.strip()
                turma_original = turma_raw.strip()

                print(f"🔍 Linha {linha}: ESCOLA='{escola_original}', SERIE='{serie_original}', TURMA='{turma_original}'")

                # Validar caracteres especiais ANTES de normalizar
                if escola_original and has_special_characters(escola_original):
                    validation_errors.append({
                        "linha": linha,
                        "erro": f"Nome da escola contém caracteres especiais inválidos: '{escola_original}'",
                        "dados": dados,
                        "tipo": "caracteres_especiais"
                    })
                    continue
                
                if serie_original and has_special_characters(serie_original):
                    validation_errors.append({
                        "linha": linha,
                        "erro": f"Nome da série contém caracteres especiais inválidos: '{serie_original}'",
                        "dados": dados,
                        "tipo": "caracteres_especiais"
                    })
                    continue
                
                if turma_original and has_special_characters(turma_original):
                    validation_errors.append({
                        "linha": linha,
                        "erro": f"Nome da turma contém caracteres especiais inválidos: '{turma_original}'",
                        "dados": dados,
                        "tipo": "caracteres_especiais"
                    })
                    continue
                
                # Normaliza dados (maiúscula, trim, remove acentos)
                nome_escola = normalize_text(escola_original)
                nome_serie = normalize_text(serie_original)
                nome_turma = normalize_text(turma_original)
                
                if not nome_escola or not nome_serie or not nome_turma:
                    validation_errors.append({
                        "linha": linha,
                        "erro": "Um ou mais campos vazios ou inválidos",
                        "dados": dados,
                        "tipo": "campo_vazio"
                    })
                    continue
                
                # Criar chave única para esta combinação
                combination_key = f"{nome_escola}|{nome_serie}|{nome_turma}"
                
                # Se já processamos esta combinação, pular (é duplicata no CSV)
                if combination_key in processed_combinations:
                    continue
                
                processed_combinations.add(combination_key)

                # Detectar nomes similares de escolas (70% de similaridade)
                # REGRA: Só detectar similaridade se SERIE e TURMA também forem iguais
                if nome_escola and nome_serie and nome_turma:
                    # Buscar escolas existentes no banco com mesma SERIE e TURMA
                    cursor.execute("""
                        SELECT DISTINCT i.i_id, i.i_nome
                        FROM instituicoes i
                        INNER JOIN turmas t ON t.t_instituicao = i.i_id
                        INNER JOIN series s ON t.t_serie = s.s_id
                        WHERE s.s_nome = %s AND t.t_nome = %s
                    """, (nome_serie, nome_turma))
                    escolas_db = [{"id": row[0], "nome": row[1]} for row in cursor.fetchall()]

                    # Filtrar escolas processadas neste CSV com mesma SERIE e TURMA
                    escolas_csv_mesma_serie_turma = [
                        {"nome": e["nome"]}
                        for e in escolas_processadas
                        if e.get("serie") == nome_serie and e.get("turma") == nome_turma
                    ]

                    # Combinar escolas do banco e do CSV (removendo duplicatas por nome)
                    nomes_unicos = set()
                    todas_escolas = []

                    for escola in escolas_db + escolas_csv_mesma_serie_turma:
                        nome_normalizado = escola["nome"]
                        if nome_normalizado not in nomes_unicos:
                            nomes_unicos.add(nome_normalizado)
                            todas_escolas.append(escola)

                    similar_names = detect_similar_names(
                        nome_escola,
                        todas_escolas,
                        threshold=0.7
                    )

                    if similar_names:
                        # Evitar adicionar duplicatas de similaridade
                        for similar in similar_names:
                            # Criar chave única para evitar duplicatas
                            similar_key = f"{linha}|{nome_escola}|{similar['nome_existente']}|{nome_serie}|{nome_turma}"

                            # Verificar se já foi adicionado
                            already_added = any(
                                s["linha"] == linha and
                                s["nome_atual"] == nome_escola and
                                s["nome_similar"] == similar["nome_existente"]
                                for s in similar_schools
                            )

                            if not already_added:
                                similar_schools.append({
                                    "linha": linha,
                                    "nome_atual": nome_escola,
                                    "nome_similar": similar["nome_existente"],
                                    "similaridade": similar["similaridade"],
                                    "id_similar": similar.get("id_existente"),
                                    "dados": dados
                                })

                    # Adicionar escola à lista de processadas (com serie e turma)
                    escola_key = f"{nome_escola}|{nome_serie}|{nome_turma}"
                    if escola_key not in [f"{e['nome']}|{e.get('serie', '')}|{e.get('turma', '')}" for e in escolas_processadas]:
                        escolas_processadas.append({
                            "nome": nome_escola,
                            "serie": nome_serie,
                            "turma": nome_turma,
                            "linha": linha
                        })

                # Busca escola
                cursor.execute("SELECT i_id FROM instituicoes WHERE i_nome = %s", (nome_escola,))
                escola_result = cursor.fetchone()
                escola_id = escola_result[0] if escola_result else None

                # Se escola já existe, adicionar aviso
                if escola_id:
                    validation_warnings.append({
                        "linha": linha,
                        "aviso": f"Escola '{nome_escola}' já existe no sistema (será reutilizada)",
                        "dados": dados,
                        "tipo": "escola_existente"
                    })

                # Busca série
                cursor.execute("SELECT s_id FROM series WHERE s_nome = %s", (nome_serie,))
                serie_result = cursor.fetchone()
                serie_id = serie_result[0] if serie_result else None

                # Se série já existe, adicionar aviso
                if serie_id:
                    validation_warnings.append({
                        "linha": linha,
                        "aviso": f"Série '{nome_serie}' já existe no sistema (será reutilizada)",
                        "dados": dados,
                        "tipo": "serie_existente"
                    })

                # Se escola e série existem, verifica turma duplicada
                if escola_id and serie_id:
                    cursor.execute(
                        "SELECT t_id FROM turmas WHERE t_nome = %s AND t_serie = %s AND t_instituicao = %s",
                        (nome_turma, serie_id, escola_id)
                    )
                    turma_result = cursor.fetchone()

                    if turma_result:
                        validation_errors.append({
                            "linha": linha,
                            "erro": f"Turma '{nome_turma}' já existe na escola '{nome_escola}' para a série '{nome_serie}'",
                            "dados": dados,
                            "tipo": "turma_duplicada"
                        })

                # Conta o que seria criado
                # Escolas: conta se não existe no banco E não foi contada ainda
                if not escola_id and nome_escola not in escolas_unicas:
                    escolas_criadas += 1
                    escolas_unicas.add(nome_escola)

                # Séries: conta se não existe no banco E não foi contada ainda
                if not serie_id and nome_serie not in series_unicas:
                    series_criadas += 1
                    series_unicas.add(nome_serie)

                # Turmas: sempre conta (cada linha é uma turma única)
                # Só não conta se já existe no banco com mesma escola, série e turma
                turma_existe = False
                if escola_id and serie_id:
                    cursor.execute(
                        "SELECT t_id FROM turmas WHERE t_nome = %s AND t_serie = %s AND t_instituicao = %s",
                        (nome_turma, serie_id, escola_id)
                    )
                    turma_existe = cursor.fetchone() is not None

                if not turma_existe:
                    turmas_criadas += 1

        all_errors = result["errors"] + validation_errors

        return {
            "success": len(validation_errors) == 0,
            "message": f"✅ Validação concluída: {escolas_criadas} escolas, {series_criadas} séries, {turmas_criadas} turmas serão criadas" if len(validation_errors) == 0 else f"❌ {len(validation_errors)} erro(s) encontrado(s)",
            "stats": {
                "total_linhas": result["total_rows"],
                "escolas_criadas": escolas_criadas,
                "series_criadas": series_criadas,
                "turmas_criadas": turmas_criadas,
                "erros": len(all_errors),
                "avisos": len(validation_warnings),
                "escolas_similares": len(similar_schools),
                "escolas_unicas_count": len(escolas_unicas),
                "series_unicas_count": len(series_unicas)
            },
            "errors": all_errors,
            "warnings": validation_warnings,
            "similar_schools": similar_schools,
            "similar_schools_count": len(similar_schools),
            "duplicates_info": duplicates if duplicates else None,
            "dry_run": True,
            "debug_info": {
                "escolas_unicas": list(escolas_unicas),
                "series_unicas": list(series_unicas),
                "processed_combinations_count": len(processed_combinations)
            }
        }

    @staticmethod
    def importar_estrutura(file_content: str, db_name: str = None) -> Dict[str, Any]:
        """
        Importa estrutura (escola, série, turma) do CSV

        Args:
            file_content: Conteúdo do arquivo CSV
            db_name: Nome do banco de dados a usar

        Returns:
            Dict com resultados da importação
        """
        # Processa CSV
        result = process_csv_data(file_content, ["ESCOLA", "SERIE", "TURMA"])

        if not result["valid_rows"]:
            return {
                "success": False,
                "message": "Nenhuma linha válida encontrada",
                "errors": result["errors"],
                "stats": {
                    "total_linhas": result["total_rows"],
                    "escolas_criadas": 0,
                    "series_criadas": 0,
                    "turmas_criadas": 0,
                    "erros": len(result["errors"])
                }
            }

        # Detecta duplicatas
        duplicates = detect_duplicates(
            [row["dados"] for row in result["valid_rows"]],
            ["ESCOLA", "SERIE", "TURMA"]
        )

        # Contadores
        escolas_criadas = 0
        series_criadas = 0
        turmas_criadas = 0
        import_errors = []

        # Cache para evitar consultas repetidas
        escolas_cache = {}
        series_cache = {}

        # Importação real
        with get_db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(f"USE {db_name}")

            for row_data in result["valid_rows"]:
                try:
                    linha = row_data["linha_original"]
                    dados = row_data["dados"]

                    # Normaliza dados
                    nome_escola = normalize_text(dados.get("ESCOLA", ""))
                    nome_serie = normalize_text(dados.get("SERIE", ""))
                    nome_turma = normalize_text(dados.get("TURMA", ""))

                    if not nome_escola or not nome_serie or not nome_turma:
                        import_errors.append({
                            "linha": linha,
                            "erro": "Um ou mais campos inválidos após normalização",
                            "dados": dados
                        })
                        continue

                    # 1. PROCESSAR ESCOLA
                    escola_id = None

                    if nome_escola in escolas_cache:
                        escola_id = escolas_cache[nome_escola]
                    else:
                        cursor.execute("SELECT i_id FROM instituicoes WHERE i_nome = %s", (nome_escola,))
                        resultado = cursor.fetchone()

                        if resultado:
                            escola_id = resultado[0]
                            escolas_cache[nome_escola] = escola_id
                        else:
                            # Coletar campos opcionais
                            nome_diretor = dados.get("NOME_DIRETOR", "").strip() or None
                            telefone = dados.get("TELEFONE", "").strip() or None
                            endereco = dados.get("ENDERECO", "").strip() or None
                            municipio = dados.get("MUNICIPIO", "").strip() or None
                            regiao = dados.get("REGIAO", "").strip() or None
                            cod_rede = dados.get("COD_REDE", "").strip() or None
                            tipo_rede = dados.get("TIPO_REDE", "").strip().upper() or None
                            indigena = dados.get("INDIGENA", "").strip() or "0"

                            # Validar tipo_rede (deve ser E, M ou 0)
                            if tipo_rede and tipo_rede not in ['E', 'M', '0']:
                                tipo_rede = None

                            # Validar indígena (deve ser 0 ou 1)
                            if indigena not in ['0', '1']:
                                indigena = '0'

                            # Converter cod_rede para int se fornecido
                            if cod_rede:
                                try:
                                    cod_rede = int(cod_rede)
                                except ValueError:
                                    cod_rede = None

                            # Inserir escola com campos opcionais
                            cursor.execute("""
                                INSERT INTO instituicoes
                                (i_nome, i_nome_diretor, i_telefone, i_endereco, i_municipio,
                                 i_regiao, i_cod_rede, i_tipo_rede, i_indigena)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """, (nome_escola, nome_diretor, telefone, endereco, municipio,
                                  regiao, cod_rede, tipo_rede, indigena))
                            escola_id = cursor.lastrowid
                            escolas_cache[nome_escola] = escola_id
                            escolas_criadas += 1

                    # 2. PROCESSAR SÉRIE
                    serie_id = None

                    if nome_serie in series_cache:
                        serie_id = series_cache[nome_serie]
                    else:
                        cursor.execute("SELECT s_id FROM series WHERE s_nome = %s", (nome_serie,))
                        resultado = cursor.fetchone()

                        if resultado:
                            serie_id = resultado[0]
                            series_cache[nome_serie] = serie_id
                        else:
                            cursor.execute("INSERT INTO series (s_nome, s_instituicao) VALUES (%s, 1)", (nome_serie,))
                            serie_id = cursor.lastrowid
                            series_cache[nome_serie] = serie_id
                            series_criadas += 1

                    # 3. PROCESSAR TURMA
                    cursor.execute(
                        "SELECT t_id FROM turmas WHERE t_nome = %s AND t_serie = %s AND t_instituicao = %s",
                        (nome_turma, serie_id, escola_id)
                    )

                    resultado_turma = cursor.fetchone()
                    if resultado_turma:
                        import_errors.append({
                            "linha": linha,
                            "erro": f"Turma '{nome_turma}' já existe",
                            "dados": dados
                        })
                        continue

                    cursor.execute(
                        "INSERT INTO turmas (t_nome, t_serie, t_instituicao) VALUES (%s, %s, %s)",
                        (nome_turma, serie_id, escola_id)
                    )
                    turmas_criadas += 1

                except Exception as e:
                    import_errors.append({
                        "linha": linha,
                        "erro": f"Erro ao processar linha: {str(e)}",
                        "dados": dados
                    })

            # Commit das transações
            if hasattr(connection, 'commit'):
                connection.commit()

        all_errors = result["errors"] + import_errors

        success_msg = f"✅ Importação concluída: {escolas_criadas} escolas, {series_criadas} séries, {turmas_criadas} turmas criadas"

        return {
            "success": True,
            "message": success_msg,
            "stats": {
                "total_linhas": result["total_rows"],
                "escolas_criadas": escolas_criadas,
                "series_criadas": series_criadas,
                "turmas_criadas": turmas_criadas,
                "erros": len(all_errors)
            },
            "errors": all_errors,
            "duplicates_info": duplicates if duplicates else None
        }

    @staticmethod
    def obter_informacoes_estrutura(db_name: str = None) -> Dict[str, Any]:
        """
        Retorna informações sobre dados existentes e formato esperado do CSV

        Args:
            db_name: Nome do banco de dados
        """
        try:
            with get_db_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(f"USE {db_name}")

                # Lista instituições
                cursor.execute("SELECT i_id, i_nome FROM instituicoes ORDER BY i_nome LIMIT 10")
                instituicoes = cursor.fetchall()

                # Lista séries
                cursor.execute("SELECT s_id, s_nome FROM series ORDER BY s_nome LIMIT 10")
                series = cursor.fetchall()

                # Lista turmas (com informações relacionadas)
                cursor.execute("""
                    SELECT t.t_id, t.t_nome, s.s_nome as serie_nome, i.i_nome as instituicao_nome
                    FROM turmas t
                    JOIN series s ON t.t_serie = s.s_id
                    JOIN instituicoes i ON t.t_instituicao = i.i_id
                    ORDER BY i.i_nome, s.s_nome, t.t_nome
                    LIMIT 10
                """)
                turmas = cursor.fetchall()

                # Contar totais
                cursor.execute("SELECT COUNT(*) as total FROM instituicoes")
                total_instituicoes = cursor.fetchone()['total']

                cursor.execute("SELECT COUNT(*) as total FROM series")
                total_series = cursor.fetchone()['total']

                cursor.execute("SELECT COUNT(*) as total FROM turmas")
                total_turmas = cursor.fetchone()['total']

                return {
                    "success": True,
                    "formato_csv": {
                        "descricao": "O CSV deve ter 3 colunas: ESCOLA,SERIE,TURMA",
                        "exemplo_cabecalho": "ESCOLA,SERIE,TURMA",
                        "exemplo_linhas": [
                            "ANDRE FRANCO MONTORO,1ANO,A",
                            "ESCOLA MUNICIPAL EXEMPLO,2ANO,B"
                        ],
                        "observacoes": [
                            "Escolas serão criadas automaticamente se não existirem",
                            "Séries serão criadas automaticamente (s_instituicao = 1)",
                            "Turmas devem ser únicas por escola+série"
                        ]
                    },
                    "dados_existentes": {
                        "instituicoes": {
                            "total": total_instituicoes,
                            "exemplos": instituicoes
                        },
                        "series": {
                            "total": total_series,
                            "exemplos": series
                        },
                        "turmas": {
                            "total": total_turmas,
                            "exemplos": turmas
                        }
                    }
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"Erro ao buscar informações: {str(e)}"
            }

