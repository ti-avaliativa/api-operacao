"""
Testes unitários para EstruturaService
"""
import pytest
from app.services.estrutura_service import EstruturaService


class TestEstruturaService:
    """Testes para o serviço de importação de estrutura"""
    
    def test_validar_estrutura_csv_valido(self):
        """Testa validação de CSV válido"""
        csv_content = """ESCOLA,SERIE,TURMA
ANDRE FRANCO MONTORO,1ANO,A
ANDRE FRANCO MONTORO,1ANO,B
ANDRE FRANCO MONTORO,2ANO,A"""
        
        result = EstruturaService.validar_estrutura_csv(csv_content, dry_run=True)
        
        assert result["success"] is True
        assert result["stats"]["total_linhas"] == 3
        assert result["stats"]["erros"] == 0
    
    def test_validar_estrutura_csv_invalido_colunas(self):
        """Testa validação de CSV com colunas inválidas"""
        csv_content = """ESCOLA,SERIE
ANDRE FRANCO MONTORO,1ANO"""
        
        result = EstruturaService.validar_estrutura_csv(csv_content, dry_run=True)
        
        assert result["success"] is False
        assert "colunas obrigatórias" in result["message"].lower()
    
    def test_validar_estrutura_csv_linha_vazia(self):
        """Testa validação de CSV com linha vazia"""
        csv_content = """ESCOLA,SERIE,TURMA
ANDRE FRANCO MONTORO,1ANO,A
,,
ANDRE FRANCO MONTORO,2ANO,A"""
        
        result = EstruturaService.validar_estrutura_csv(csv_content, dry_run=True)
        
        assert result["success"] is True
        assert result["stats"]["total_linhas"] == 2  # Linha vazia ignorada
    
    def test_validar_estrutura_csv_caracteres_especiais(self):
        """Testa validação de CSV com caracteres especiais"""
        csv_content = """ESCOLA,SERIE,TURMA
ESCOLA@#$,1ANO,A"""
        
        result = EstruturaService.validar_estrutura_csv(csv_content, dry_run=True)
        
        assert result["success"] is False
        assert result["stats"]["erros"] > 0
    
    def test_normalizar_texto(self):
        """Testa normalização de texto"""
        from app.utils.text_utils import normalize_text
        
        assert normalize_text("  ESCOLA  ") == "ESCOLA"
        assert normalize_text("escola") == "ESCOLA"
        assert normalize_text("Escola") == "ESCOLA"
    
    def test_obter_informacoes_estrutura(self):
        """Testa obtenção de informações sobre estrutura"""
        result = EstruturaService.obter_informacoes_estrutura()
        
        assert result["success"] is True
        assert "formato_csv" in result["data"]
        assert "exemplo" in result["data"]


class TestAlunosService:
    """Testes para o serviço de importação de alunos"""
    
    def test_step1_upload_validacao_sucesso(self):
        """Testa step 1 com arquivo válido"""
        from app.services.alunos_service import AlunosService
        
        csv_content = """RA,NOME,ESCOLA,SERIE,TURMA
12345,JOAO SILVA,ANDRE FRANCO MONTORO,1ANO,A
67890,MARIA SANTOS,ANDRE FRANCO MONTORO,1ANO,B"""
        
        result = AlunosService.step1_upload_validacao(
            filename="alunos.csv",
            file_content=csv_content,
            file_size=len(csv_content)
        )
        
        assert result["success"] is True
        assert result["step"] == 1
        assert "session_id" in result
    
    def test_step1_arquivo_muito_grande(self):
        """Testa step 1 com arquivo muito grande"""
        from app.services.alunos_service import AlunosService
        
        result = AlunosService.step1_upload_validacao(
            filename="alunos.csv",
            file_content="teste",
            file_size=11 * 1024 * 1024  # 11 MB
        )
        
        assert result["success"] is False
        assert "muito grande" in result["message"].lower()
    
    def test_step1_arquivo_vazio(self):
        """Testa step 1 com arquivo vazio"""
        from app.services.alunos_service import AlunosService
        
        result = AlunosService.step1_upload_validacao(
            filename="alunos.csv",
            file_content="",
            file_size=0
        )
        
        assert result["success"] is False
        assert "vazio" in result["message"].lower()


class TestTextUtils:
    """Testes para utilitários de texto"""
    
    def test_normalize_text(self):
        """Testa normalização de texto"""
        from app.utils.text_utils import normalize_text
        
        assert normalize_text("  texto  ") == "TEXTO"
        assert normalize_text("TeXtO") == "TEXTO"
        assert normalize_text("") == ""
    
    def test_has_special_characters(self):
        """Testa detecção de caracteres especiais"""
        from app.utils.text_utils import has_special_characters
        
        assert has_special_characters("texto@#$") is True
        assert has_special_characters("TEXTO NORMAL") is False
        assert has_special_characters("TEXTO-NORMAL") is False
    
    def test_calculate_similarity(self):
        """Testa cálculo de similaridade"""
        from app.utils.text_utils import calculate_similarity
        
        assert calculate_similarity("JOAO", "JOAO") == 1.0
        assert calculate_similarity("JOAO", "JOÃO") > 0.8
        assert calculate_similarity("JOAO", "MARIA") < 0.5


class TestCSVProcessor:
    """Testes para processador de CSV"""
    
    def test_process_csv_data(self):
        """Testa processamento de CSV"""
        from app.utils.csv_processor import process_csv_data
        
        csv_content = """ESCOLA,SERIE,TURMA
ANDRE FRANCO MONTORO,1ANO,A
ANDRE FRANCO MONTORO,1ANO,B"""
        
        result = process_csv_data(csv_content)
        
        assert result["success"] is True
        assert len(result["rows"]) == 2
    
    def test_detect_duplicates(self):
        """Testa detecção de duplicatas"""
        from app.utils.csv_processor import detect_duplicates
        
        rows = [
            {"ESCOLA": "ESCOLA1", "SERIE": "1ANO", "TURMA": "A"},
            {"ESCOLA": "ESCOLA1", "SERIE": "1ANO", "TURMA": "A"},  # Duplicata
            {"ESCOLA": "ESCOLA1", "SERIE": "2ANO", "TURMA": "A"},
        ]
        
        duplicates = detect_duplicates(rows, ["ESCOLA", "SERIE", "TURMA"])
        
        assert len(duplicates) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

