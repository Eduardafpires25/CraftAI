import pytest
from unittest.mock import Mock, patch, MagicMock
from pydantic import BaseModel, Field

from src.api.ai.client import AIClient
from src.api.ai.schemas import AIError


class SchemaForTesting(BaseModel):
    """Schema de teste para complete_with_schema."""
    name: str = Field(..., description="Nome")
    value: int = Field(..., description="Valor")


class TestAIClient:
    """Testes para AIClient."""

    def test_init_with_defaults(self):
        """Testa inicialização com valores padrão."""
        with patch('src.api.ai.client.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.OPENAI_BASE_URL = "https://api.openai.com"
            mock_settings.OPENAI_TEXT_MODEL = "gpt-4"
            mock_settings.OPENAI_IMAGE_MODEL = "dall-e-3"
            mock_settings.OPENAI_IMAGE_SIZE = "1024x1024"
            mock_settings.OPENAI_TIMEOUT_SECONDS = 60
            
            client = AIClient()
            assert client.api_key == "test-key"
            assert client.base_url == "https://api.openai.com"
            assert client.text_model == "gpt-4"
            assert client.image_model == "dall-e-3"
            assert client.image_size == "1024x1024"
            assert client.timeout == 60

    def test_init_with_custom_values(self):
        """Testa inicialização com valores customizados."""
        client = AIClient(
            api_key="test-key",
            base_url="https://test.com",
            text_model="gpt-4",
            image_model="dall-e-3",
            image_size="512x512",
            timeout=30.0,
        )
        assert client.api_key == "test-key"
        assert client.base_url == "https://test.com"
        assert client.text_model == "gpt-4"
        assert client.image_model == "dall-e-3"
        assert client.image_size == "512x512"
        assert client.timeout == 30.0

    def test_init_without_api_key_logs_warning(self):
        """Testa que inicialização sem API key loga warning."""
        with patch('src.api.ai.client.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = None
            mock_settings.OPENAI_BASE_URL = "https://api.openai.com"
            mock_settings.OPENAI_TEXT_MODEL = "gpt-4"
            mock_settings.OPENAI_IMAGE_MODEL = "dall-e-3"
            mock_settings.OPENAI_IMAGE_SIZE = "1024x1024"
            mock_settings.OPENAI_TIMEOUT_SECONDS = 60
            
            with patch('src.api.ai.client.logger') as mock_logger:
                client = AIClient()
                mock_logger.warning.assert_called_with("AIClient inicializado sem OPENAI_API_KEY definida.")

    def test_generate_image_empty_prompt(self):
        """Testa erro ao gerar imagem com prompt vazio."""
        client = AIClient()
        with pytest.raises(AIError, match="prompt para geração de imagem não pode ser vazio"):
            client.generate_image("")

    def test_generate_image_whitespace_prompt(self):
        """Testa erro ao gerar imagem com prompt só com espaços."""
        client = AIClient()
        with pytest.raises(AIError, match="prompt para geração de imagem não pode ser vazio"):
            client.generate_image("   ")

    def test_generate_image_api_error(self):
        """Testa erro na chamada da API."""
        client = AIClient()
        with patch.object(client._client.images, 'generate', side_effect=Exception("API Error")):
            with pytest.raises(AIError, match="Falha ao gerar imagem"):
                client.generate_image("test prompt")

    def test_generate_image_empty_response(self):
        """Testa erro quando API retorna resposta vazia."""
        client = AIClient()
        mock_response = Mock()
        mock_response.data = []
        
        with patch.object(client._client.images, 'generate', return_value=mock_response):
            with pytest.raises(AIError, match="Provider retornou resposta vazia"):
                client.generate_image("test prompt")

    def test_generate_image_success(self):
        """Testa geração de imagem com sucesso."""
        client = AIClient(
            api_key="test-key",
            base_url="https://api.openai.com",
            text_model="gpt-4",
            image_model="dall-e-3",
            image_size="1024x1024",
            timeout=30.0,
        )
        
        mock_item = Mock()
        mock_item.url = "https://example.com/image.png"
        mock_item.b64_json = None
        mock_item.revised_prompt = "revised prompt"
        
        mock_response = Mock()
        mock_response.data = [mock_item]
        mock_response.model_dump.return_value = {"data": [mock_item]}
        
        with patch.object(client._client.images, 'generate', return_value=mock_response):
            with patch('src.api.ai.client.time.perf_counter', side_effect=[0, 0.1]):
                result = client.generate_image("test prompt")
                
                assert result.model == client.image_model
                assert result.prompt == "test prompt"
                assert result.url == "https://example.com/image.png"
                assert result.revised_prompt == "revised prompt"
                assert result.b64_json is None
                assert result.size == client.image_size
                assert result.duration_ms == 100

    def test_generate_image_with_b64_json(self):
        """Testa geração de imagem com b64_json."""
        client = AIClient()
        
        mock_item = Mock()
        mock_item.url = None
        mock_item.b64_json = "base64string"
        mock_item.revised_prompt = None
        
        mock_response = Mock()
        mock_response.data = [mock_item]
        mock_response.model_dump.return_value = {"data": [mock_item]}
        
        with patch.object(client._client.images, 'generate', return_value=mock_response):
            result = client.generate_image("test prompt", response_format="b64_json")
            
            assert result.b64_json == "base64string"
            assert result.url is None

    def test_generate_image_custom_params(self):
        """Testa geração de imagem com parâmetros customizados."""
        client = AIClient()
        
        mock_item = Mock()
        mock_item.url = "https://example.com/image.png"
        mock_item.b64_json = None
        mock_item.revised_prompt = None
        
        mock_response = Mock()
        mock_response.data = [mock_item]
        mock_response.model_dump.return_value = {"data": [mock_item]}
        
        with patch.object(client._client.images, 'generate', return_value=mock_response) as mock_gen:
            result = client.generate_image(
                "test prompt",
                model="dall-e-3",
                size="512x512",
                n=2,
                extra={"quality": "hd"},
            )
            
            mock_gen.assert_called_once()
            call_kwargs = mock_gen.call_args[1]
            assert call_kwargs["model"] == "dall-e-3"
            assert call_kwargs["size"] == "512x512"
            assert call_kwargs["n"] == 2
            assert call_kwargs["quality"] == "hd"

    def test_build_iteration_prompt_with_product_type(self):
        """Testa construção de prompt com tipo de produto."""
        prompt = AIClient._build_iteration_prompt("custom mug with logo", "mug")
        assert prompt == "Customizable mug design: custom mug with logo"

    def test_build_iteration_prompt_without_product_type(self):
        """Testa construção de prompt sem tipo de produto."""
        prompt = AIClient._build_iteration_prompt("custom design with flowers", None)
        assert prompt == "Custom artisanal design: custom design with flowers"

    def test_build_iteration_prompt_whitespace(self):
        """Testa construção de prompt com espaços."""
        prompt = AIClient._build_iteration_prompt("  custom design  ", "mug")
        assert prompt == "Customizable mug design: custom design"

    def test_generate_iteration_image_placeholder_mode(self):
        """Testa geração de imagem em modo placeholder."""
        client = AIClient()
        
        with patch('src.api.ai.client.settings') as mock_settings:
            mock_settings.AI_PLACEHOLDER_MODE = True
            
            result = client.generate_iteration_image("test description", "mug")
            
            assert result.model == "placeholder-green"
            assert result.image_bytes is not None
            assert result.content_type == "image/png"
            assert result.cost_usd == 0.0
            assert result.duration_ms >= 0

    def test_generate_iteration_image_real_mode_no_b64(self):
        """Testa erro quando API não retorna b64_json."""
        client = AIClient()
        
        mock_result = Mock()
        mock_result.b64_json = None
        mock_result.prompt = "test prompt"
        mock_result.model = "dall-e-3"
        mock_result.duration_ms = 1000
        
        with patch('src.api.ai.client.settings') as mock_settings:
            mock_settings.AI_PLACEHOLDER_MODE = False
            with patch.object(client, 'generate_image', return_value=mock_result):
                with pytest.raises(AIError, match="Provider nao retornou b64_json"):
                    client.generate_iteration_image("test description", "mug")

    def test_generate_iteration_image_real_mode_success(self):
        """Testa geração de imagem em modo real com sucesso."""
        client = AIClient()
        
        mock_result = Mock()
        mock_result.b64_json = "aGVsbG8="  # base64 de "hello"
        mock_result.prompt = "test prompt"
        mock_result.model = "dall-e-3"
        mock_result.duration_ms = 1000
        
        with patch('src.api.ai.client.settings') as mock_settings:
            mock_settings.AI_PLACEHOLDER_MODE = False
            with patch.object(client, 'generate_image', return_value=mock_result):
                result = client.generate_iteration_image("test description", "mug")
                
                assert result.model == "dall-e-3"
                assert result.image_bytes is not None
                assert result.content_type == "image/png"
                assert result.prompt == "test prompt"
                assert result.duration_ms == 1000

    def test_complete_with_schema_invalid_schema(self):
        """Testa erro ao passar schema inválido."""
        client = AIClient()
        
        with pytest.raises(AIError, match="schema deve ser uma subclasse de pydantic.BaseModel"):
            client.complete_with_schema("test", "not a schema")

    def test_complete_with_schema_api_error(self):
        """Testa erro na chamada da API."""
        client = AIClient()
        
        with patch.object(client._client.beta.chat.completions, 'parse', side_effect=Exception("API Error")):
            with pytest.raises(AIError, match="Falha na completion estruturada"):
                client.complete_with_schema("test", SchemaForTesting)

    def test_complete_with_schema_empty_choices(self):
        """Testa erro quando API retorna sem choices."""
        client = AIClient()
        
        mock_response = Mock()
        mock_response.choices = []
        
        with patch.object(client._client.beta.chat.completions, 'parse', return_value=mock_response):
            with pytest.raises(AIError, match="Provider retornou resposta sem choices"):
                client.complete_with_schema("test", SchemaForTesting)

    def test_complete_with_schema_none_parsed(self):
        """Testa erro quando parsed é None."""
        client = AIClient()
        
        mock_choice = Mock()
        mock_choice.message.parsed = None
        mock_choice.message.refusal = "Model refused"
        
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        
        with patch.object(client._client.beta.chat.completions, 'parse', return_value=mock_response):
            with pytest.raises(AIError, match="Modelo recusou ou não retornou parse válido"):
                client.complete_with_schema("test", SchemaForTesting)

    def test_complete_with_schema_string_message(self):
        """Testa completion com mensagem como string."""
        client = AIClient()
        
        mock_parsed = SchemaForTesting(name="test", value=42)
        mock_choice = Mock()
        mock_choice.message.parsed = mock_parsed
        mock_choice.message.refusal = None
        
        mock_usage = Mock()
        mock_usage.prompt_tokens = 10
        mock_usage.completion_tokens = 20
        mock_usage.total_tokens = 30
        
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage
        mock_response.model_dump.return_value = {}
        
        with patch.object(client._client.beta.chat.completions, 'parse', return_value=mock_response):
            result = client.complete_with_schema("test message", SchemaForTesting)
            
            assert result.parsed.name == "test"
            assert result.parsed.value == 42
            assert result.prompt_tokens == 10
            assert result.completion_tokens == 20
            assert result.total_tokens == 30
            assert result.duration_ms >= 0

    def test_complete_with_schema_list_messages(self):
        """Testa completion com lista de mensagens."""
        client = AIClient()
        
        mock_parsed = SchemaForTesting(name="test", value=42)
        mock_choice = Mock()
        mock_choice.message.parsed = mock_parsed
        mock_choice.message.refusal = None
        
        mock_usage = Mock()
        mock_usage.prompt_tokens = 10
        mock_usage.completion_tokens = 20
        mock_usage.total_tokens = 30
        
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage
        mock_response.model_dump.return_value = {}
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "test message"},
        ]
        
        with patch.object(client._client.beta.chat.completions, 'parse', return_value=mock_response):
            result = client.complete_with_schema(messages, SchemaForTesting)
            
            assert result.parsed.name == "test"
            assert result.parsed.value == 42

    def test_complete_with_schema_system_prompt(self):
        """Testa completion com system prompt."""
        client = AIClient()
        
        mock_parsed = SchemaForTesting(name="test", value=42)
        mock_choice = Mock()
        mock_choice.message.parsed = mock_parsed
        mock_choice.message.refusal = None
        
        mock_usage = Mock()
        mock_usage.prompt_tokens = 10
        mock_usage.completion_tokens = 20
        mock_usage.total_tokens = 30
        
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage
        mock_response.model_dump.return_value = {}
        
        with patch.object(client._client.beta.chat.completions, 'parse', return_value=mock_response) as mock_parse:
            result = client.complete_with_schema("test", SchemaForTesting, system_prompt="You are helpful")
            
            # Verifica que o system prompt foi adicionado
            call_kwargs = mock_parse.call_args[1]
            assert call_kwargs["messages"][0]["role"] == "system"
            assert call_kwargs["messages"][0]["content"] == "You are helpful"

    def test_complete_with_schema_custom_model(self):
        """Testa completion com modelo customizado."""
        client = AIClient()
        
        mock_parsed = SchemaForTesting(name="test", value=42)
        mock_choice = Mock()
        mock_choice.message.parsed = mock_parsed
        mock_choice.message.refusal = None
        
        mock_usage = Mock()
        mock_usage.prompt_tokens = 10
        mock_usage.completion_tokens = 20
        mock_usage.total_tokens = 30
        
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage
        mock_response.model_dump.return_value = {}
        
        with patch.object(client._client.beta.chat.completions, 'parse', return_value=mock_response) as mock_parse:
            result = client.complete_with_schema("test", SchemaForTesting, model="gpt-4")
            
            call_kwargs = mock_parse.call_args[1]
            assert call_kwargs["model"] == "gpt-4"

    def test_complete_with_schema_extra_params(self):
        """Testa completion com parâmetros extras."""
        client = AIClient()
        
        mock_parsed = SchemaForTesting(name="test", value=42)
        mock_choice = Mock()
        mock_choice.message.parsed = mock_parsed
        mock_choice.message.refusal = None
        
        mock_usage = Mock()
        mock_usage.prompt_tokens = 10
        mock_usage.completion_tokens = 20
        mock_usage.total_tokens = 30
        
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage
        mock_response.model_dump.return_value = {}
        
        with patch.object(client._client.beta.chat.completions, 'parse', return_value=mock_response) as mock_parse:
            result = client.complete_with_schema("test", SchemaForTesting, extra={"max_tokens": 100})
            
            call_kwargs = mock_parse.call_args[1]
            assert call_kwargs["max_tokens"] == 100
