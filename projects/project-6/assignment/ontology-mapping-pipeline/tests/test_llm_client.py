"""
Tests for the LLM client module.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.llm.client import (
    LLMClient,
    LLMResponse,
    ClaudeClient,
    OpenAIClient,
    create_llm_client,
)
from src.llm.prompts import (
    SYSTEM_PROMPT,
    CANDIDATE_GENERATION_PROMPT,
    SCORING_PROMPT,
    format_prompt,
)
from src.llm.parsers import (
    extract_json,
    parse_candidate_response,
    parse_scoring_response,
    CandidateGenerationResponse,
    ScoringResponse,
)


class TestLLMResponse:
    """Tests for LLMResponse dataclass."""
    
    def test_create_response(self):
        """Test creating an LLM response."""
        response = LLMResponse(
            content="Test response",
            model="claude-sonnet-4-20250514",
            usage={"input_tokens": 100, "output_tokens": 50},
        )
        
        assert response.content == "Test response"
        assert response.model == "claude-sonnet-4-20250514"
        assert response.usage["input_tokens"] == 100


class TestClaudeClient:
    """Tests for Claude client."""
    
    @pytest.mark.asyncio
    async def test_complete_with_mock(self):
        """Test completion with mocked Anthropic client."""
        with patch("src.llm.client.AsyncAnthropic") as mock_anthropic:
            # Setup mock
            mock_client = AsyncMock()
            mock_anthropic.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="Test response")]
            mock_response.model = "claude-sonnet-4-20250514"
            mock_response.usage.input_tokens = 100
            mock_response.usage.output_tokens = 50
            
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            
            # Create client and test
            client = ClaudeClient({
                "api_key": "test-key",
                "model": "claude-sonnet-4-20250514",
            })
            
            response = await client.complete("Test prompt")
            
            assert response.content == "Test response"
            mock_client.messages.create.assert_called_once()
    
    def test_missing_api_key(self):
        """Test that missing API key raises error."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
                ClaudeClient({"model": "claude-sonnet-4-20250514"})


class TestOpenAIClient:
    """Tests for OpenAI client."""
    
    @pytest.mark.asyncio
    async def test_complete_with_mock(self):
        """Test completion with mocked OpenAI client."""
        with patch("src.llm.client.AsyncOpenAI") as mock_openai:
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.choices = [
                MagicMock(message=MagicMock(content="Test response"))
            ]
            mock_response.model = "gpt-4"
            mock_response.usage.prompt_tokens = 100
            mock_response.usage.completion_tokens = 50
            
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            
            client = OpenAIClient({
                "api_key": "test-key",
                "model": "gpt-4",
            })
            
            response = await client.complete("Test prompt")
            
            assert response.content == "Test response"


class TestPromptFormatting:
    """Tests for prompt formatting."""
    
    def test_format_candidate_prompt(self):
        """Test formatting candidate generation prompt."""
        prompt = format_prompt(
            CANDIDATE_GENERATION_PROMPT,
            source_iri="http://example.org/source#Dog",
            source_label="Dog",
            source_definition="A domesticated mammal",
            source_synonyms="Canine, Hound",
            source_parents="Animal",
            target_concepts="- Cat\n- Wolf",
        )
        
        assert "Dog" in prompt
        assert "http://example.org/source#Dog" in prompt
        assert "domesticated mammal" in prompt
    
    def test_format_with_missing_optional(self):
        """Test formatting with missing optional fields."""
        # Should not raise, missing fields get default values
        prompt = format_prompt(
            CANDIDATE_GENERATION_PROMPT,
            source_iri="http://example.org/test",
            source_label="Test",
            source_definition="Test definition",
            target_concepts="- Target1",
        )
        
        assert "Test" in prompt
        assert "None provided" in prompt  # Default for missing optionals


class TestResponseParsing:
    """Tests for response parsing."""
    
    def test_extract_json_from_code_block(self):
        """Test extracting JSON from markdown code block."""
        text = """Here is the response:
```json
{"key": "value"}
```
"""
        result = extract_json(text)
        assert result == '{"key": "value"}'
    
    def test_extract_json_raw(self):
        """Test extracting raw JSON."""
        text = '{"key": "value"}'
        result = extract_json(text)
        assert result == '{"key": "value"}'
    
    def test_parse_candidate_response_success(self):
        """Test parsing valid candidate response."""
        response_text = """
{
    "mappings": [
        {
            "target_iri": "http://example.org/target#Canine",
            "predicate": "skos:exactMatch",
            "confidence": 0.95,
            "justification": "Both refer to dogs"
        }
    ],
    "no_match_reason": null
}
"""
        result = parse_candidate_response(response_text)
        
        assert isinstance(result, CandidateGenerationResponse)
        assert len(result.mappings) == 1
        assert result.mappings[0].confidence == 0.95
        assert result.mappings[0].predicate == "skos:exactMatch"
    
    def test_parse_candidate_response_no_matches(self):
        """Test parsing response with no matches."""
        response_text = """
{
    "mappings": [],
    "no_match_reason": "No suitable matches found in target ontology"
}
"""
        result = parse_candidate_response(response_text)
        
        assert len(result.mappings) == 0
        assert "No suitable matches" in result.no_match_reason
    
    def test_parse_candidate_response_invalid(self):
        """Test parsing invalid response returns empty."""
        result = parse_candidate_response("not valid json {{{")
        
        assert isinstance(result, CandidateGenerationResponse)
        assert len(result.mappings) == 0
        assert result.no_match_reason is not None
    
    def test_parse_scoring_response(self):
        """Test parsing scoring response."""
        response_text = """
{
    "scores": {
        "lexical": 0.8,
        "semantic": 0.9,
        "structural": 0.7,
        "predicate_fit": 0.85
    },
    "overall_score": 0.82,
    "recommended_predicate": "skos:exactMatch",
    "reasoning": "High semantic similarity based on definitions"
}
"""
        result = parse_scoring_response(response_text)
        
        assert isinstance(result, ScoringResponse)
        assert result.scores.lexical == 0.8
        assert result.overall_score == 0.82
        assert result.recommended_predicate == "skos:exactMatch"


class TestClientFactory:
    """Tests for client factory function."""
    
    def test_create_claude_client(self, tmp_path):
        """Test creating Claude client from config."""
        config_content = """
provider: anthropic
anthropic:
    api_key: test-key
    model: claude-sonnet-4-20250514
"""
        config_path = tmp_path / "llm_config.yaml"
        config_path.write_text(config_content)
        
        with patch("src.llm.client.AsyncAnthropic"):
            client = create_llm_client(str(config_path))
            assert isinstance(client, ClaudeClient)
    
    def test_create_openai_client(self, tmp_path):
        """Test creating OpenAI client from config."""
        config_content = """
provider: openai
openai:
    api_key: test-key
    model: gpt-4
"""
        config_path = tmp_path / "llm_config.yaml"
        config_path.write_text(config_content)
        
        with patch("src.llm.client.AsyncOpenAI"):
            client = create_llm_client(str(config_path))
            assert isinstance(client, OpenAIClient)
    
    def test_unknown_provider_raises(self, tmp_path):
        """Test that unknown provider raises error."""
        config_content = """
provider: unknown_provider
"""
        config_path = tmp_path / "llm_config.yaml"
        config_path.write_text(config_content)
        
        with pytest.raises(ValueError, match="Unknown provider"):
            create_llm_client(str(config_path))
