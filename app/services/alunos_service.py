"""
Serviço de importação de alunos
Responsabilidade: Lógica de negócio para importação de alunos (multi-step)
"""
import time
from datetime import datetime
from typing import Dict, Any, List
from app.core.database import get_db_connection
from app.utils.text_utils import normalize_text, has_special_characters, detect_similar_names, validate_email
from app.utils.csv_processor import parse_csv_basic

# Cache global para sessões de importação
import_sessions = {}


class AlunosService:
    """Serviço para gerenciar importação de alunos (processo multi-step)"""
    
    @staticmethod
    def step1_upload_validacao(filename: str, file_content: str, file_size: int, db_name: str = None) -> Dict[str, Any]:
        """
        Passo 1: Upload e validação inicial do arquivo CSV de alunos

        Args:
            filename: Nome do arquivo
            file_content: Conteúdo do arquivo
            file_size: Tamanho do arquivo em bytes
            db_name: Nome do banco de dados

        Returns:
            Dict com resultado da validação e session_id
        """
        try:
            # Validação do arquivo
            if not filename.lower().endswith('.csv'):
                return {
                    "success": False,
                    "message": "Formato de arquivo inválido. Apenas arquivos CSV são aceitos.",
                    "step": 1
                }
            
            if file_size > 25 * 1024 * 1024:  # 25MB
                return {
                    "success": False,
                    "message": "Arquivo muito grande. Tamanho máximo: 25MB.",
                    "step": 1
                }
            
            # Parse básico do CSV
            parse_result = parse_csv_basic(file_content)
            
            if not parse_result["success"]:
                return {
                    "success": False,
                    "message": parse_result["message"],
                    "step": 1
                }
            
            headers = parse_result["headers"]
            data_rows = parse_result["data_rows"]

            # Normalizar dados: converter para maiúsculas e fazer trim
            normalized_rows = []
            for row in data_rows:
                normalized_row = []
                for cell in row:
                    if isinstance(cell, str):
                        # Converter para maiúsculas e remover espaços no início/fim
                        normalized_cell = cell.upper().strip()
                        normalized_row.append(normalized_cell)
                    else:
                        normalized_row.append(cell)
                normalized_rows.append(normalized_row)

            # Cria sessão de importação
            session_id = f"import_{int(time.time())}_{filename}"
            import_sessions[session_id] = {
                "step": 1,
                "filename": filename,
                "headers": headers,
                "data_rows": normalized_rows,  # Usar dados normalizados
                "total_rows": len(normalized_rows),
                "created_at": datetime.now().isoformat(),
                "mapping": {},
                "validation_results": None,
                "conflicts": [],
                "import_results": None,
                "db_name": db_name  # Armazenar db_name na sessão
            }
            
            return {
                "success": True,
                "message": f"Arquivo processado com sucesso! {len(normalized_rows)} registros encontrados.",
                "step": 1,
                "session_id": session_id,
                "data": {
                    "filename": filename,
                    "total_rows": len(normalized_rows),
                    "headers": headers,
                    "preview": normalized_rows[:5]  # Primeiras 5 linhas
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Erro no processamento do arquivo: {str(e)}",
                "step": 1
            }
    
    @staticmethod
    def step2_validar_mapeamento(session_id: str, mapping: dict, db_name: str = None) -> Dict[str, Any]:
        """
        Passo 2: Validação do mapeamento de colunas

        Args:
            session_id: ID da sessão de importação
            mapping: Dicionário com mapeamento de colunas
            db_name: Nome do banco de dados

        Returns:
            Dict com resultado da validação
        """
        try:
            print(f"🔍 DEBUG - Verificando sessão: {session_id}")
            print(f"🔍 DEBUG - Sessões disponíveis: {list(import_sessions.keys())}")

            if session_id not in import_sessions:
                return {
                    "success": False,
                    "message": f"Sessão de importação não encontrada ou expirada. Session ID: {session_id}",
                    "step": 2,
                    "debug": {
                        "session_id_received": session_id,
                        "available_sessions": list(import_sessions.keys())
                    }
                }

            session = import_sessions[session_id]

            # Debug: ver o que está chegando
            print(f"🔍 DEBUG - Mapeamento recebido: {mapping}")
            print(f"🔍 DEBUG - Tipo do mapeamento: {type(mapping)}")
            print(f"🔍 DEBUG - Headers da sessão: {session['headers']}")
            print(f"🔍 DEBUG - Tipo dos headers: {type(session['headers'])}")
            
            # Converter mapeamento do formato do frontend (nome_coluna: 'NOME_ALUNO')
            # para o formato interno (coluna_index: 'nome')
            headers = session["headers"]
            internal_mapping = {}
            
            # Mapear cada campo
            field_mappings = {
                'nome_coluna': 'nome',
                'ra_coluna': 'ra',
                'email_coluna': 'email',
                'instituicao_coluna': 'escola',
                'serie_coluna': 'serie',
                'turma_coluna': 'turma',
                'senha_coluna': 'senha',
                'numero_chamada_coluna': 'numero_chamada',
                'portador_necessidade_coluna': 'portador_necessidade'
            }
            
            for frontend_key, internal_field in field_mappings.items():
                column_name = mapping.get(frontend_key)
                if column_name:
                    # Encontrar o índice da coluna nos headers
                    try:
                        print(f"🔍 Procurando '{column_name}' (tipo: {type(column_name)}) em {headers}")
                        col_index = headers.index(column_name)
                        internal_mapping[str(col_index)] = internal_field
                        print(f"✅ Mapeado: {frontend_key}='{column_name}' -> índice {col_index} -> campo '{internal_field}'")
                    except ValueError as e:
                        print(f"❌ Coluna '{column_name}' não encontrada nos headers: {headers}")
                        print(f"❌ Erro: {e}")
                        # Tentar encontrar com strip() para remover espaços
                        column_name_stripped = column_name.strip() if isinstance(column_name, str) else column_name
                        headers_stripped = [h.strip() if isinstance(h, str) else h for h in headers]
                        print(f"🔍 Tentando com strip: '{column_name_stripped}' em {headers_stripped}")
                        try:
                            col_index = headers_stripped.index(column_name_stripped)
                            internal_mapping[str(col_index)] = internal_field
                            print(f"✅ Mapeado (com strip): {frontend_key}='{column_name}' -> índice {col_index} -> campo '{internal_field}'")
                        except ValueError:
                            print(f"❌ Ainda não encontrado mesmo com strip")
                            pass  # Coluna não encontrada nos headers
            
            print(f"🔍 DEBUG - Mapeamento interno criado: {internal_mapping}")
            
            # Validação dos campos obrigatórios
            required_fields = ['nome', 'escola', 'serie', 'turma', 'ra']
            mapped_fields = list(internal_mapping.values())
            
            print(f"🔍 DEBUG - Campos obrigatórios: {required_fields}")
            print(f"🔍 DEBUG - Campos mapeados: {mapped_fields}")

            missing_fields = [field for field in required_fields if field not in mapped_fields]
            if missing_fields:
                return {
                    "success": False,
                    "message": f"Campos obrigatórios não mapeados: {', '.join(missing_fields)}",
                    "step": 2,
                    "missing_fields": missing_fields
                }
            
            # Salva mapeamento interno na sessão
            session["mapping"] = internal_mapping
            session["step"] = 2
            # Atualizar db_name se fornecido
            if db_name:
                session["db_name"] = db_name
            
            return {
                "success": True,
                "message": "Mapeamento validado com sucesso!",
                "step": 2,
                "session_id": session_id,
                "data": {
                    "mapping": internal_mapping,
                    "required_fields": required_fields,
                    "total_rows": session["total_rows"]
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Erro na validação do mapeamento: {str(e)}",
                "step": 2
            }

    @staticmethod
    def step3_validar_detectar_conflitos(session_id: str, db_name: str = None) -> Dict[str, Any]:
        """
        Passo 3: Validação e detecção de conflitos

        Args:
            session_id: ID da sessão de importação
            db_name: Nome do banco de dados

        Returns:
            Dict com resultado da validação e conflitos detectados
        """
        try:
            if session_id not in import_sessions:
                return {
                    "success": False,
                    "message": "Sessão de importação não encontrada.",
                    "step": 3
                }

            session = import_sessions[session_id]
            if session["step"] < 2:
                return {
                    "success": False,
                    "message": "É necessário completar o mapeamento primeiro.",
                    "step": 3
                }

            # Usar db_name da sessão ou do parâmetro
            if db_name:
                session["db_name"] = db_name
            db_name = session.get("db_name")

            headers = session["headers"]
            data_rows = session["data_rows"]
            mapping = session["mapping"]

            # Mapear colunas para índices
            field_indices = {}
            for col_index, field in mapping.items():
                if field != "NULO":
                    field_indices[field] = int(col_index)

            validation_results = {
                "valid_rows": [],
                "invalid_rows": [],
                "warnings": [],
                "conflicts": [],
                "duplicates": [],  # Duplicatas no arquivo
                "special_chars_errors": [],  # Erros de caracteres especiais
                "similar_names": []  # Nomes similares (warnings)
            }

            # Validar cada linha
            with get_db_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(f"USE {db_name}")

                # Verificar se estamos em modo DEMO
                cursor.execute("SELECT 1")
                result = cursor.fetchone()

                # Verificar se o banco tem dados reais
                # Se não houver escolas cadastradas, assumir modo DEMO
                cursor.execute("SELECT COUNT(*) as total FROM instituicoes")
                count_result = cursor.fetchone()
                has_data = count_result and count_result['total'] > 0

                demo_mode = not has_data
                print(f"🔍 Modo de operação: {'DEMO (sem dados no banco)' if demo_mode else 'PRODUÇÃO (com dados no banco)'}")

                # Cache para detectar RAs duplicados no mesmo arquivo
                ras_encontrados = {}
                # Cache para detectar duplicatas completas (todas as colunas iguais)
                rows_hash = {}
                # Cache para detectar nomes similares
                nomes_processados = []
                
                for row_index, row in enumerate(data_rows):
                    try:
                        row_data = {}
                        is_valid = True
                        row_errors = []

                        # Extrair dados da linha baseado no mapeamento
                        for field, col_index in field_indices.items():
                            if col_index < len(row):
                                value = row[col_index].strip()

                                # Email: manter minúsculas, apenas trim
                                if field == 'email':
                                    value = value.lower().strip()

                                row_data[field] = value

                                # Validação de campos obrigatórios
                                if field in ['nome', 'escola', 'serie', 'turma', 'ra'] and not value:
                                    is_valid = False
                                    row_errors.append(f"Campo '{field}' é obrigatório")

                                # Validação de email (se preenchido)
                                if field == 'email' and value:
                                    email_validation = validate_email(value)
                                    if not email_validation["valid"]:
                                        is_valid = False
                                        row_errors.append(email_validation["error"])

                                # Validação de caracteres especiais em campos de texto (exceto email)
                                if field in ['nome', 'escola', 'serie', 'turma'] and value:
                                    if has_special_characters(value):
                                        is_valid = False
                                        row_errors.append(f"Campo '{field}' contém caracteres especiais não permitidos: '{value}'")
                                        validation_results["special_chars_errors"].append({
                                            "row_index": row_index,
                                            "field": field,
                                            "value": value,
                                            "data": row_data.copy()
                                        })
                            else:
                                row_data[field] = ""
                                if field in ['nome', 'escola', 'serie', 'turma', 'ra']:
                                    is_valid = False
                                    row_errors.append(f"Campo '{field}' não encontrado")

                        # Detectar duplicatas completas (todas as colunas iguais)
                        row_hash = "|".join([str(row_data.get(f, "")) for f in ['nome', 'ra', 'escola', 'serie', 'turma']])
                        if row_hash in rows_hash:
                            # Linha duplicada encontrada
                            validation_results["duplicates"].append({
                                "row_index": row_index,
                                "duplicate_of": rows_hash[row_hash],
                                "data": row_data.copy()
                            })
                            # Ignorar linha duplicada (não processar)
                            continue
                        else:
                            rows_hash[row_hash] = row_index

                        # Detectar nomes similares (70% de similaridade)
                        if row_data.get('nome'):
                            similar_names = detect_similar_names(
                                row_data['nome'],
                                nomes_processados,
                                threshold=0.7
                            )

                            if similar_names:
                                for similar in similar_names:
                                    validation_results["similar_names"].append({
                                        "row_index": row_index,
                                        "nome_atual": row_data['nome'],
                                        "nome_similar": similar["nome_existente"],
                                        "similaridade": similar["similaridade"],
                                        "linha_similar": similar.get("row_index"),
                                        "data": row_data.copy()
                                    })

                            # Adicionar nome ao cache
                            nomes_processados.append({
                                "nome": row_data['nome'],
                                "row_index": row_index
                            })

                        if is_valid:
                            # Verificar se entidades obrigatórias existem
                            if demo_mode:
                                # Em modo DEMO, aceitar qualquer escola/série/turma
                                # (não fazer validação de existência)
                                print(f"🔍 DEMO MODE - Aceitando linha {row_index}: {row_data}")
                                pass  # Aceitar todos os dados em modo DEMO
                            else:
                                # Verificar escola
                                cursor.execute("SELECT i_id FROM instituicoes WHERE i_nome = %s", (row_data['escola'],))
                                escola_exists = cursor.fetchone()
                                if not escola_exists:
                                    is_valid = False
                                    row_errors.append(f"Escola '{row_data['escola']}' não existe no sistema")

                                # Verificar série
                                cursor.execute("SELECT s_id FROM series WHERE s_nome = %s", (row_data['serie'],))
                                serie_exists = cursor.fetchone()
                                if not serie_exists:
                                    is_valid = False
                                    row_errors.append(f"Série '{row_data['serie']}' não existe no sistema")

                                # Verificar turma (se escola e série existem)
                                if escola_exists and serie_exists:
                                    cursor.execute(
                                        "SELECT t_id FROM turmas WHERE t_nome = %s AND t_serie = %s AND t_instituicao = %s",
                                        (row_data['turma'], serie_exists['s_id'], escola_exists['i_id'])
                                    )
                                    turma_exists = cursor.fetchone()
                                    if not turma_exists:
                                        is_valid = False
                                        row_errors.append(f"Turma '{row_data['turma']}' não existe para a escola '{row_data['escola']}' e série '{row_data['serie']}'")

                        if is_valid:
                            # Verificar conflitos com dados existentes
                            conflicts = []
                            
                            ra = row_data.get('ra', '')
                            
                            # Verificar se RA está duplicado no próprio arquivo
                            if ra:
                                if ra in ras_encontrados:
                                    conflicts.append({
                                        "type": "ra_duplicado_arquivo",
                                        "field": "ra", 
                                        "value": ra,
                                        "message": f"RA '{ra}' está duplicado no arquivo (linha {ras_encontrados[ra] + 1} e {row_index + 1})",
                                        "duplicate_row": ras_encontrados[ra]
                                    })
                                else:
                                    ras_encontrados[ra] = row_index

                            # Verificar se aluno já existe por RA (matrícula)
                            if 'ra' in row_data and row_data['ra']:
                                if demo_mode:
                                    # Em modo DEMO, simular que não há conflitos iniciais
                                    aluno_existente = None
                                else:
                                    cursor.execute(
                                        "SELECT a.a_id, a.a_usuario, u.u_nome FROM alunos a INNER JOIN usuarios u ON u.u_id = a.a_usuario WHERE a.a_matricula = %s", 
                                        (row_data['ra'],)
                                    )
                                    aluno_existente = cursor.fetchone()
                                
                                if aluno_existente:
                                    conflicts.append({
                                        "type": "aluno_duplicado",
                                        "field": "ra",
                                        "value": row_data['ra'],
                                        "message": f"Aluno com RA '{row_data['ra']}' já existe no sistema (Nome: {aluno_existente['u_nome']})",
                                        "existing_id": aluno_existente['a_id'],
                                        "existing_name": aluno_existente['u_nome']
                                    })

                            validation_results["valid_rows"].append({
                                "row_index": row_index,
                                "data": row_data,
                                "conflicts": conflicts
                            })

                            if conflicts:
                                validation_results["conflicts"].extend([{
                                    "row_index": row_index,
                                    **conflict
                                } for conflict in conflicts])

                        else:
                            validation_results["invalid_rows"].append({
                                "row_index": row_index,
                                "data": row_data,
                                "errors": row_errors
                            })

                    except Exception as e:
                        validation_results["invalid_rows"].append({
                            "row_index": row_index,
                            "data": {},
                            "errors": [f"Erro no processamento da linha: {str(e)}"]
                        })

            # Salvar resultados na sessão
            session["validation_results"] = validation_results
            session["conflicts"] = validation_results["conflicts"]
            session["step"] = 3

            # Log dos resultados
            print(f"📊 Validação concluída:")
            print(f"   ✅ Linhas válidas: {len(validation_results['valid_rows'])}")
            print(f"   ❌ Linhas inválidas: {len(validation_results['invalid_rows'])}")
            print(f"   ⚠️  Conflitos: {len(validation_results['conflicts'])}")
            print(f"   🔄 Duplicatas: {len(validation_results['duplicates'])}")
            print(f"   ⚠️  Caracteres especiais: {len(validation_results['special_chars_errors'])}")
            print(f"   👥 Nomes similares: {len(validation_results['similar_names'])}")

            if validation_results["invalid_rows"]:
                print(f"\n❌ Detalhes das linhas inválidas:")
                for invalid_row in validation_results["invalid_rows"][:5]:  # Mostrar apenas as primeiras 5
                    print(f"   Linha {invalid_row['row_index']}: {invalid_row['errors']}")
                    print(f"   Dados: {invalid_row['data']}")

            return {
                "success": True,
                "message": "Validação concluída com sucesso!",
                "step": 3,
                "session_id": session_id,
                "data": {
                    "valid_rows": len(validation_results["valid_rows"]),
                    "invalid_rows": len(validation_results["invalid_rows"]),
                    "conflicts_count": len(validation_results["conflicts"]),
                    "duplicates_count": len(validation_results["duplicates"]),
                    "special_chars_count": len(validation_results["special_chars_errors"]),
                    "similar_names_count": len(validation_results["similar_names"]),
                    "conflicts": validation_results["conflicts"][:10],
                    "invalid_rows_data": validation_results["invalid_rows"][:20],  # Retornar até 20 linhas inválidas
                    "duplicates": validation_results["duplicates"][:10],  # Retornar até 10 duplicatas
                    "special_chars_errors": validation_results["special_chars_errors"][:10],  # Retornar até 10 erros de caracteres especiais
                    "similar_names": validation_results["similar_names"][:20],  # Retornar até 20 nomes similares
                    "summary": {
                        "total_rows": len(data_rows),
                        "total_linhas": len(data_rows),
                        "linhas_validas": len(validation_results["valid_rows"]),
                        "linhas_invalidas": len(validation_results["invalid_rows"]),
                        "conflitos_detectados": len(validation_results["conflicts"]),
                        "duplicatas_detectadas": len(validation_results["duplicates"]),
                        "caracteres_especiais": len(validation_results["special_chars_errors"]),
                        "nomes_similares": len(validation_results["similar_names"])
                    }
                }
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Erro na validação: {str(e)}",
                "step": 3
            }

    @staticmethod
    def step4_resolver_conflitos(session_id: str, conflict_resolutions: dict, db_name: str = None) -> Dict[str, Any]:
        """
        Passo 4: Resolução de conflitos

        Args:
            session_id: ID da sessão de importação
            conflict_resolutions: Dicionário com resoluções de conflitos
            db_name: Nome do banco de dados

        Returns:
            Dict com resultado da resolução
        """
        try:
            if session_id not in import_sessions:
                return {
                    "success": False,
                    "message": "Sessão de importação não encontrada.",
                    "step": 4
                }

            session = import_sessions[session_id]
            if session["step"] < 3:
                return {
                    "success": False,
                    "message": "É necessário completar a validação primeiro.",
                    "step": 4
                }

            # Atualizar db_name se fornecido
            if db_name:
                session["db_name"] = db_name

            # Aplicar resoluções de conflitos
            validation_results = session["validation_results"]
            resolutions_applied = 0

            for row_index_str, resolution in conflict_resolutions.items():
                row_index = int(row_index_str)
                
                # Encontrar a linha correspondente
                for valid_row in validation_results["valid_rows"]:
                    if valid_row["row_index"] == row_index:
                        # Aplicar resolução baseada no tipo
                        if resolution.get("action") == "skip":
                            # Marcar linha para pular na importação
                            valid_row["skip_import"] = True
                            resolutions_applied += 1
                        elif resolution.get("action") == "import_anyway":
                            # Importar mesmo com conflito (RA duplicado será informado)
                            valid_row["import_with_conflict"] = True
                            resolutions_applied += 1
                        elif resolution.get("action") == "update_existing":
                            # Marcar linha para atualizar registro existente
                            valid_row["update_existing"] = True
                            resolutions_applied += 1
                        break

            # Remover conflitos das linhas que tiveram resolução
            remaining_conflicts = []
            for conflict in validation_results["conflicts"]:
                conflict_resolved = False
                for row_index_str in conflict_resolutions.keys():
                    if conflict["row_index"] == int(row_index_str):
                        conflict_resolved = True
                        break
                if not conflict_resolved:
                    remaining_conflicts.append(conflict)
                    
            validation_results["conflicts"] = remaining_conflicts

            # Atualizar sessão
            session["validation_results"] = validation_results
            session["step"] = 4

            return {
                "success": True,
                "message": "Conflitos resolvidos com sucesso!",
                "step": 4,
                "session_id": session_id,
                "data": {
                    "resolutions_applied": resolutions_applied,
                    "remaining_conflicts": len(remaining_conflicts),
                    "ready_for_import": True,
                    "total_rows_to_import": len([row for row in validation_results["valid_rows"] if not row.get("skip_import", False)])
                }
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Erro na resolução de conflitos: {str(e)}",
                "step": 4
            }

    @staticmethod
    def step5_importar_final(session_id: str, db_name: str = None) -> Dict[str, Any]:
        """
        Passo 5: Importação final dos alunos

        Args:
            session_id: ID da sessão de importação
            db_name: Nome do banco de dados

        Returns:
            Dict com resultado da importação
        """
        try:
            if session_id not in import_sessions:
                return {
                    "success": False,
                    "message": "Sessão de importação não encontrada.",
                    "step": 5
                }

            session = import_sessions[session_id]
            if session["step"] < 3:
                return {
                    "success": False,
                    "message": "É necessário completar a validação primeiro.",
                    "step": 5
                }

            # Usar db_name da sessão ou do parâmetro
            if db_name:
                session["db_name"] = db_name
            db_name = session.get("db_name")

            validation_results = session["validation_results"]
            valid_rows = validation_results["valid_rows"]

            # Filtrar apenas linhas que devem ser importadas
            rows_to_import = [row for row in valid_rows if not row.get("skip_import", False)]

            import_results = {
                "alunos_criados": 0,
                "alunos_com_ra_duplicado": 0,
                "erros": [],
                "detalhes": []
            }

            with get_db_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(f"USE {db_name}")
                
                # Verificar se estamos em modo DEMO
                cursor.execute("SELECT 1")
                demo_mode = cursor.fetchone() is None
                
                if hasattr(connection, 'autocommit'):
                    connection.autocommit = False  # Usar transações
                
                try:
                    for row in rows_to_import:
                        try:
                            data = row["data"]
                            
                            # Pular se foi marcada para pular
                            if row.get("skip_import", False):
                                continue
                            
                            if demo_mode:
                                # Simular importação em modo DEMO
                                ra = data.get("ra", "")
                                nome = data.get("nome", "")
                                
                                # Simular verificação de RA duplicado (apenas alguns RAs como exemplo)
                                if ra in ["202401001"]:  # Apenas o primeiro RA como "existente"
                                    import_results["alunos_com_ra_duplicado"] += 1
                                    import_results["detalhes"].append({
                                        "row_index": row["row_index"],
                                        "ra": ra,
                                        "nome": nome,
                                        "status": "RA já existe (DEMO)",
                                        "nome_existente": "Aluno Simulado"
                                    })
                                    continue
                                
                                # Simular criação bem-sucedida
                                import_results["alunos_criados"] += 1
                                import_results["detalhes"].append({
                                    "row_index": row["row_index"],
                                    "ra": ra,
                                    "nome": nome,
                                    "status": "Importado com sucesso (DEMO)",
                                    "aluno_id": f"demo_{row['row_index']}"
                                })
                                continue
                                
                            # Obter IDs das entidades (que já foram validadas como existentes)
                            cursor.execute("SELECT i_id FROM instituicoes WHERE i_nome = %s", (data["escola"],))
                            escola = cursor.fetchone()
                            escola_id = escola["i_id"]
                            
                            cursor.execute("SELECT s_id FROM series WHERE s_nome = %s", (data["serie"],))
                            serie = cursor.fetchone()
                            serie_id = serie["s_id"]
                            
                            cursor.execute(
                                "SELECT t_id FROM turmas WHERE t_nome = %s AND t_serie = %s AND t_instituicao = %s",
                                (data["turma"], serie_id, escola_id)
                            )
                            turma = cursor.fetchone()
                            turma_id = turma["t_id"]
                            
                            ra = data.get("ra", "")
                            nome = data.get("nome", "")
                            email = data.get("email", "")
                            senha = data.get("senha", "123456")  # Senha padrão se não fornecida
                            
                            # Verificar se RA já existe
                            cursor.execute(
                                "SELECT a.a_id, u.u_nome FROM alunos a INNER JOIN usuarios u ON u.u_id = a.a_usuario WHERE a.a_matricula = %s", 
                                (ra,)
                            )
                            aluno_existente = cursor.fetchone()
                            
                            if aluno_existente:
                                import_results["alunos_com_ra_duplicado"] += 1
                                import_results["detalhes"].append({
                                    "row_index": row["row_index"],
                                    "ra": ra,
                                    "nome": nome,
                                    "status": "RA já existe",
                                    "nome_existente": aluno_existente["u_nome"]
                                })
                                continue
                            
                            # 1. Criar/obter email se fornecido
                            email_id = None
                            if email:
                                cursor.execute("SELECT e_id FROM emails WHERE e_endereco = %s", (email,))
                                email_existente = cursor.fetchone()
                                if email_existente:
                                    email_id = email_existente["e_id"]
                                else:
                                    cursor.execute(
                                        "INSERT INTO emails (e_endereco, e_confirmado) VALUES (%s, 0)", 
                                        (email,)
                                    )
                                    email_id = cursor.lastrowid
                            
                            # 2. Criar usuário
                            cursor.execute(
                                "INSERT INTO usuarios (u_login, u_senha, u_nome, u_email, u_grupos, u_instituicao) VALUES (%s, %s, %s, %s, %s, %s)",
                                (ra, senha, nome, email_id, 4, escola_id)
                            )
                            usuario_id = cursor.lastrowid
                            
                            # 3. Criar aluno
                            numero_chamada = data.get("numero_chamada", None)
                            portador_necessidade = 1 if data.get("portador_necessidade", "").lower() in ["sim", "s", "1", "true"] else 0
                            
                            cursor.execute(
                                "INSERT INTO alunos (a_usuario, a_matricula, a_turma, a_numero_chamada, a_portador_necessidade) VALUES (%s, %s, %s, %s, %s)",
                                (usuario_id, ra, turma_id, numero_chamada, portador_necessidade)
                            )
                            aluno_id = cursor.lastrowid
                            
                            import_results["alunos_criados"] += 1
                            import_results["detalhes"].append({
                                "row_index": row["row_index"],
                                "ra": ra,
                                "nome": nome,
                                "status": "Importado com sucesso",
                                "aluno_id": aluno_id
                            })
                            
                        except Exception as e:
                            import_results["erros"].append({
                                "row_index": row["row_index"],
                                "ra": data.get("ra", ""),
                                "nome": data.get("nome", ""),
                                "error": str(e)
                            })
                    
                    # Commit das transações
                    if hasattr(connection, 'commit'):
                        connection.commit()
                    
                except Exception as e:
                    # Rollback em caso de erro
                    if hasattr(connection, 'rollback'):
                        connection.rollback()
                    raise e

            # Salvar resultados na sessão
            session["import_results"] = import_results
            session["step"] = 5

            return {
                "success": True,
                "message": f"Importação concluída! {import_results['alunos_criados']} alunos criados. {import_results['alunos_com_ra_duplicado']} com RA já existente.",
                "step": 5,
                "session_id": session_id,
                "data": import_results
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Erro na importação: {str(e)}",
                "step": 5
            }

    @staticmethod
    def obter_status_importacao(session_id: str) -> Dict[str, Any]:
        """
        Obtém o status de uma sessão de importação

        Args:
            session_id: ID da sessão de importação

        Returns:
            Dict com status da sessão
        """
        if session_id not in import_sessions:
            return {
                "success": False,
                "message": "Sessão de importação não encontrada."
            }

        session = import_sessions[session_id]

        return {
            "success": True,
            "session_id": session_id,
            "data": {
                "step": session["step"],
                "filename": session["filename"],
                "total_rows": session["total_rows"],
                "created_at": session["created_at"],
                "validation_results": session.get("validation_results"),
                "import_results": session.get("import_results")
            }
        }

