"""
API Handler for BotManager V2.5 - Enhanced AI Project Generator with Multi-Bot Support

This module provides a centralized API handler for managing various AI service APIs.
It handles API key management, rate limiting, error handling, and response parsing.
"""

import os
import json
import time
import logging
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from enum import Enum
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError
import openai
from openai import OpenAI
import anthropic
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APIProvider(Enum):
    """Enumeration of supported API providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    REPLICATE = "replicate"
    HUGGINGFACE = "huggingface"
    CUSTOM = "custom"


class APIModel(Enum):
    """Enumeration of available models for each provider."""
    # OpenAI models
    GPT4_TURBO = "gpt-4-turbo-preview"
    GPT4 = "gpt-4"
    GPT35_TURBO = "gpt-3.5-turbo"
    
    # Anthropic models
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"
    
    # Google models
    GEMINI_PRO = "gemini-pro"
    GEMINI_ULTRA = "gemini-ultra"
    
    # Replicate models
    LLAMA_2_70B = "llama-2-70b"
    MISTRAL_7B = "mistral-7b"
    
    # HuggingFace models
    ZEPHYR_7B = "zephyr-7b"
    FALCON_7B = "falcon-7b"


@dataclass
class APIResponse:
    """Data class for standardized API responses."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    tokens_used: Optional[int] = None
    latency: Optional[float] = None
    raw_response: Optional[Dict] = None


@dataclass
class APIConfig:
    """Data class for API configuration."""
    provider: APIProvider
    model: str
    api_key: str
    base_url: Optional[str] = None
    max_tokens: int = 2048
    temperature: float = 0.7
    timeout: int = 30
    max_retries: int = 3


class APIHandler:
    """
    Main API handler class for managing multiple AI service APIs.
    
    Features:
    - Unified interface for multiple AI providers
    - Automatic API key management from environment variables
    - Rate limiting and retry logic
    - Response caching (optional)
    - Token usage tracking
    - Fallback provider support
    """
    
    def __init__(self, cache_enabled: bool = False, cache_ttl: int = 300):
        """
        Initialize the API handler.
        
        Args:
            cache_enabled: Whether to enable response caching
            cache_ttl: Cache time-to-live in seconds
        """
        self.cache_enabled = cache_enabled
        self.cache_ttl = cache_ttl
        self.response_cache: Dict[str, tuple[float, APIResponse]] = {}
        
        # Initialize API clients
        self.openai_client = None
        self.anthropic_client = None
        self.google_client = None
        
        # API usage tracking
        self.usage_stats: Dict[str, Dict[str, Any]] = {}
        
        # Load API keys from environment variables (Replit Secrets)
        self._load_api_keys()
        
        logger.info("API Handler initialized")
    
    def _load_api_keys(self) -> None:
        """Load API keys from environment variables."""
        self.api_keys = {
            APIProvider.OPENAI: os.getenv("OPENAI_API_KEY"),
            APIProvider.ANTHROPIC: os.getenv("ANTHROPIC_API_KEY"),
            APIProvider.GOOGLE: os.getenv("GOOGLE_API_KEY"),
            APIProvider.REPLICATE: os.getenv("REPLICATE_API_KEY"),
            APIProvider.HUGGINGFACE: os.getenv("HUGGINGFACE_API_KEY"),
        }
        
        # Log which APIs are available
        available_apis = []
        for provider, key in self.api_keys.items():
            if key:
                available_apis.append(provider.value)
        
        logger.info(f"Available APIs: {', '.join(available_apis) if available_apis else 'None'}")
    
    def _get_cache_key(self, provider: str, model: str, prompt: str) -> str:
        """Generate a cache key for the given parameters."""
        import hashlib
        key_string = f"{provider}:{model}:{prompt}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _check_cache(self, cache_key: str) -> Optional[APIResponse]:
        """Check if response is in cache and still valid."""
        if not self.cache_enabled:
            return None
        
        if cache_key in self.response_cache:
            timestamp, response = self.response_cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                logger.debug(f"Cache hit for key: {cache_key[:16]}...")
                return response
        
        return None
    
    def _update_cache(self, cache_key: str, response: APIResponse) -> None:
        """Update the response cache."""
        if self.cache_enabled:
            self.response_cache[cache_key] = (time.time(), response)
            # Clean old cache entries
            self._clean_cache()
    
    def _clean_cache(self) -> None:
        """Remove expired cache entries."""
        current_time = time.time()
        expired_keys = [
            key for key, (timestamp, _) in self.response_cache.items()
            if current_time - timestamp > self.cache_ttl
        ]
        for key in expired_keys:
            del self.response_cache[key]
    
    def _update_usage_stats(self, provider: str, model: str, tokens: int) -> None:
        """Update usage statistics."""
        provider_key = f"{provider}_{model}"
        if provider_key not in self.usage_stats:
            self.usage_stats[provider_key] = {
                "total_requests": 0,
                "total_tokens": 0,
                "successful_requests": 0,
                "failed_requests": 0
            }
        
        stats = self.usage_stats[provider_key]
        stats["total_requests"] += 1
        stats["total_tokens"] += tokens
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((RequestException, Timeout, ConnectionError))
    )
    def _make_request_with_retry(self, func, *args, **kwargs) -> Any:
        """Make an API request with retry logic."""
        return func(*args, **kwargs)
    
    def _initialize_openai_client(self) -> None:
        """Initialize OpenAI client if not already initialized."""
        if not self.openai_client and self.api_keys[APIProvider.OPENAI]:
            self.openai_client = OpenAI(api_key=self.api_keys[APIProvider.OPENAI])
    
    def _initialize_anthropic_client(self) -> None:
        """Initialize Anthropic client if not already initialized."""
        if not self.anthropic_client and self.api_keys[APIProvider.ANTHROPIC]:
            self.anthropic_client = anthropic.Anthropic(
                api_key=self.api_keys[APIProvider.ANTHROPIC]
            )
    
    def _initialize_google_client(self) -> None:
        """Initialize Google client if not already initialized."""
        if not self.google_client and self.api_keys[APIProvider.GOOGLE]:
            genai.configure(api_key=self.api_keys[APIProvider.GOOGLE])
            self.google_client = genai
    
    def call_openai(self, config: APIConfig, prompt: str, system_prompt: Optional[str] = None) -> APIResponse:
        """Make a call to OpenAI API."""
        start_time = time.time()
        
        try:
            self._initialize_openai_client()
            if not self.openai_client:
                return APIResponse(
                    success=False,
                    error="OpenAI API key not configured",
                    provider=config.provider.value,
                    model=config.model
                )
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self._make_request_with_retry(
                self.openai_client.chat.completions.create,
                model=config.model,
                messages=messages,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                timeout=config.timeout
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else None
            
            latency = time.time() - start_time
            
            # Update usage stats
            if tokens_used:
                self._update_usage_stats(config.provider.value, config.model, tokens_used)
            
            return APIResponse(
                success=True,
                data=content,
                provider=config.provider.value,
                model=config.model,
                tokens_used=tokens_used,
                latency=latency,
                raw_response=response.model_dump() if hasattr(response, 'model_dump') else None
            )
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return APIResponse(
                success=False,
                error=str(e),
                provider=config.provider.value,
                model=config.model,
                latency=time.time() - start_time
            )
    
    def call_anthropic(self, config: APIConfig, prompt: str, system_prompt: Optional[str] = None) -> APIResponse:
        """Make a call to Anthropic API."""
        start_time = time.time()
        
        try:
            self._initialize_anthropic_client()
            if not self.anthropic_client:
                return APIResponse(
                    success=False,
                    error="Anthropic API key not configured",
                    provider=config.provider.value,
                    model=config.model
                )
            
            messages = [{"role": "user", "content": prompt}]
            
            response = self._make_request_with_retry(
                self.anthropic_client.messages.create,
                model=config.model,
                max_tokens=config.max_tokens,
                messages=messages,
                system=system_prompt,
                temperature=config.temperature
            )
            
            content = response.content[0].text
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            
            latency = time.time() - start_time
            
            # Update usage stats
            self._update_usage_stats(config.provider.value, config.model, tokens_used)
            
            return APIResponse(
                success=True,
                data=content,
                provider=config.provider.value,
                model=config.model,
                tokens_used=tokens_used,
                latency=latency,
                raw_response=response.model_dump() if hasattr(response, 'model_dump') else None
            )
            
        except Exception as e:
            logger.error(f"Anthropic API error: {str(e)}")
            return APIResponse(
                success=False,
                error=str(e),
                provider=config.provider.value,
                model=config.model,
                latency=time.time() - start_time
            )
    
    def call_google(self, config: APIConfig, prompt: str, system_prompt: Optional[str] = None) -> APIResponse:
        """Make a call to Google Gemini API."""
        start_time = time.time()
        
        try:
            self._initialize_google_client()
            if not self.google_client:
                return APIResponse(
                    success=False,
                    error="Google API key not configured",
                    provider=config.provider.value,
                    model=config.model
                )
            
            model = self.google_client.GenerativeModel(config.model)
            
            # Combine system prompt and user prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            response = self._make_request_with_retry(
                model.generate_content,
                full_prompt,
                generation_config={
                    "temperature": config.temperature,
                    "max_output_tokens": config.max_tokens,
                }
            )
            
            content = response.text
            # Google API doesn't provide token usage in free tier
            tokens_used = None
            
            latency = time.time() - start_time
            
            return APIResponse(
                success=True,
                data=content,
                provider=config.provider.value,
                model=config.model,
                tokens_used=tokens_used,
                latency=latency,
                raw_response=response.__dict__ if hasattr(response, '__dict__') else None
            )
            
        except Exception as e:
            logger.error(f"Google API error: {str(e)}")
            return APIResponse(
                success=False,
                error=str(e),
                provider=config.provider.value,
                model=config.model,
                latency=time.time() - start_time
            )
    
    def call_replicate(self, config: APIConfig, prompt: str, system_prompt: Optional[str] = None) -> APIResponse:
        """Make a call to Replicate API."""
        start_time = time.time()
        
        try:
            api_key = self.api_keys[APIProvider.REPLICATE]
            if not api_key:
                return APIResponse(
                    success=False,
                    error="Replicate API key not configured",
                    provider=config.provider.value,
                    model=config.model
                )
            
            headers = {
                "Authorization": f"Token {api_key}",
                "Content-Type": "application/json"
            }
            
            # Map model names to Replicate model IDs
            model_map = {
                APIModel.LLAMA_2_70B.value: "meta/llama-2-70b-chat",
                APIModel.MISTRAL_7B.value: "mistralai/mistral-7b-instruct-v0.1"
            }
            
            model_id = model_map.get(config.model, config.model)
            
            # Combine system prompt and user prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            payload = {
                "version": model_id,
                "input": {
                    "prompt": full_prompt,
                    "max_length": config.max_tokens,
                    "temperature": config.temperature
                }
            }
            
            # Start prediction
            response = self._make_request_with_retry(
                requests.post,
                "https://api.replicate.com/v1/predictions",
                headers=headers,
                json=payload,
                timeout=config.timeout
            )
            response.raise_for_status()
            
            prediction = response.json()
            prediction_id = prediction["id"]
            
            # Poll for completion
            for _ in range(30):  # Max 30 attempts
                time.sleep(1)
                status_response = requests.get(
                    f"https://api.replicate.com/v1/predictions/{prediction_id}",
                    headers=headers,
                    timeout=config.timeout
                )
                status_response.raise_for_status()
                
                status_data = status_response.json()
                if status_data["status"] == "succeeded":
                    content = "".join(status_data["output"])
                    latency = time.time() - start_time
                    
                    return APIResponse(
                        success=True,
                        data=content,
                        provider=config.provider.value,
                        model=config.model,
                        latency=latency,
                        raw_response=status_data
                    )
                elif status_data["status"] in ["failed", "canceled"]:
                    raise Exception(f"Prediction {status_data['status']}: {status_data.get('error', 'Unknown error')}")
            
            raise TimeoutError("Prediction timed out")
            
        except Exception as e:
            logger.error(f"Replicate API error: {str(e)}")
            return APIResponse(
                success=False,
                error=str(e),
                provider=config.provider.value,
                model=config.model,
                latency=time.time() - start_time
            )
    
    def call_huggingface(self, config: APIConfig, prompt: str, system_prompt: Optional[str] = None) -> APIResponse:
        """Make a call to HuggingFace Inference API."""
        start_time = time.time()
        
        try:
            api_key = self.api_keys[APIProvider.HUGGINGFACE]
            if not api_key:
                return APIResponse(
                    success=False,
                    error="HuggingFace API key not configured",
                    provider=config.provider.value,
                    model=config.model
                )
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # Map model names to HuggingFace model IDs
            model_map = {
                APIModel.ZEPHYR_7B.value: "HuggingFaceH4/zephyr-7b-beta",
                APIModel.FALCON_7B.value: "tiiuae/falcon-7b-instruct"
            }
            
            model_id = model_map.get(config.model, config.model)
            
            # Combine system prompt and user prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            payload = {
                "inputs": full_prompt,
                "parameters": {
                    "max_new_tokens": config.max_tokens,
                    "temperature": config.temperature,
                    "return_full_text": False
                }
            }
            
            response = self._make_request_with_retry(
                requests.post,
                f"https://api-inference.huggingface.co/models/{model_id}",
                headers=headers,
                json=payload,
                timeout=config.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            content = result[0]["generated_text"] if isinstance(result, list) else result.get("generated_text", "")
            
            latency = time.time() - start_time
            
            return APIResponse(
                success=True,
                data=content,
                provider=config.provider.value,
                model=config.model,
                latency=latency,
                raw_response=result
            )
            
        except Exception as e:
            logger.error(f"HuggingFace API error: {str(e)}")
            return APIResponse(
                success=False,
                error=str(e),
                provider=config.provider.value,
                model=config.model,
                latency=time.time() - start_time
            )
    
    def call_custom_api(self, config: APIConfig, prompt: str, system_prompt: Optional[str] = None) -> APIResponse:
        """Make a call to a custom API endpoint."""
        start_time = time.time()
        
        try:
            if not config.base_url:
                return APIResponse(
                    success=False,
                    error="Custom API requires base_url",
                    provider=config.provider.value,
                    model=config.model
                )
            
            headers = {
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json"
            }
            
            # Combine system prompt and user prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            payload = {
                "model": config.model,
                "prompt": full_prompt,
                "max_tokens": config.max_tokens,
                "temperature": config.temperature
            }
            
            response = self._make_request_with_retry(
                requests.post,
                config.base_url,
                headers=headers,
                json=payload,
                timeout=config.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            content = result.get("choices", [{}])[0].get("text", result.get("response", ""))
            
            latency = time.time() - start_time
            
            return APIResponse(
                success=True,
                data=content,
                provider=config.provider.value,
                model=config.model,
                latency=latency,
                raw_response=result
            )
            
        except Exception as e:
            logger.error(f"Custom API error: {str(e)}")
            return APIResponse(
                success=False,
                error=str(e),
                provider=config.provider.value,
                model=config.model,
                latency=time.time() - start_time
            )
    
    def generate_response(
        self,
        prompt: str,
        provider: Union[APIProvider, str] = APIProvider.OPENAI,
        model: Union[APIModel, str] = APIModel.GPT35_TURBO,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        timeout: int = 30,
        fallback_providers: Optional[List[Union[APIProvider, str]]] = None,
        use_cache: bool = True
    ) -> APIResponse:
        """
        Generate a response using the specified AI provider.
        
        Args:
            prompt: The user prompt/message
            provider: The API provider to use
            model: The model to use
            system_prompt: Optional system prompt for context
            max_tokens: Maximum tokens in response
            temperature: Creativity temperature (0.0 to 1.0)
            timeout: Request timeout in seconds
            fallback_providers: List of fallback providers if primary fails
            use_cache: Whether to use response caching
        
        Returns:
            APIResponse object with the result
        """
        # Convert string inputs to enum if needed
        if isinstance(provider, str):
            provider = APIProvider(provider.lower())
        if isinstance(model, str):
            model = model  # Keep as string for flexibility
        
        # Check cache first
        cache_key = None
        if use_cache and self.cache_enabled:
            cache_key = self._get_cache_key(provider.value, model, prompt)
            cached_response = self._check_cache(cache_key)
            if cached_response:
                cached_response.data = f"[CACHED RESPONSE]\n{cached_response.data}"
                return cached_response
        
        # Get API key for the provider
        api_key = self.api_keys.get(provider)
        if not api_key and provider != APIProvider.CUSTOM:
            # Try fallback providers
            if fallback_providers:
                for fallback in fallback_providers:
                    fallback_key = self.api_keys.get(
                        APIProvider(fallback) if isinstance(fallback, str) else fallback
                    )
                    if fallback_key:
                        logger.info(f"Falling back to {fallback} provider")
                        provider = fallback if isinstance(fallback, APIProvider) else APIProvider(fallback)
                        api_key = fallback_key
                        break
        
        # Create config
        config = APIConfig(
            provider=provider,
            model=model,
            api_key=api_key or "",
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout
        )
        
        # Call the appropriate API
        response = None
        try:
            if provider == APIProvider.OPENAI:
                response = self.call_openai(config, prompt, system_prompt)
            elif provider == APIProvider.ANTHROPIC:
                response = self.call_anthropic(config, prompt, system_prompt)
            elif provider == APIProvider.GOOGLE:
                response = self.call_google(config, prompt, system_prompt)
            elif provider == APIProvider.REPLICATE:
                response = self.call_replicate(config, prompt, system_prompt)
            elif provider == APIProvider.HUGGINGFACE:
                response = self.call_huggingface(config, prompt, system_prompt)
            elif provider == APIProvider.CUSTOM:
                response = self.call_custom_api(config, prompt, system_prompt)
            else:
                response = APIResponse(
                    success=False,
                    error=f"Unsupported provider: {provider}",
                    provider=provider.value,
                    model=model
                )
        except Exception as e:
            logger.error(f"Unexpected error in generate_response: {str(e)}")
            response = APIResponse(
                success=False,
                error=f"Unexpected error: {str(e)}",
                provider=provider.value,
                model=model
            )
        
        # Update cache if successful
        if cache_key and response and response.success:
            self._update_cache(cache_key, response)
        
        return response
    
    def get_available_providers(self) -> List[str]:
        """Get list of available API providers with configured keys."""
        available = []
        for provider, key in self.api_keys.items():
            if key:
                available.append(provider.value)
        return available
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics for all API calls."""
        return self.usage_stats.copy()
    
    def clear_cache(self) -> None:
        """Clear the response cache."""
        self.response_cache.clear()
        logger.info("Response cache cleared")
    
    def test_connection(self, provider: Union[APIProvider, str]) -> bool:
        """Test connection to a specific API provider."""
        if isinstance(provider, str):
            provider = APIProvider(provider.lower())
        
        test_prompt = "Hello, please respond with 'OK' if you can hear me."
        
        try:
            response = self.generate_response(
                prompt=test_prompt,
                provider=provider,
                model=APIModel.GPT35_TURBO.value if provider == APIProvider.OPENAI else 
                     APIModel.CLAUDE_3_HAIKU.value if provider == APIProvider.ANTHROPIC else
                     APIModel.GEMINI_PRO.value if provider == APIProvider.GOOGLE else
                     "test-model",
                max_tokens=10,
                temperature=0,
                use_cache=False
            )
            
            return response.success and "OK" in response.data.upper()
            
        except Exception as e:
            logger.error(f"Connection test failed for {provider}: {str(e)}")
            return False
    
    def batch_generate(
        self,
        prompts: List[str],
        provider: Union[APIProvider, str] = APIProvider.OPENAI,
        model: Union[APIModel, str] = APIModel.GPT35_TURBO,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> List[APIResponse]:
        """
        Generate responses for multiple prompts.
        
        Args:
            prompts: List of prompts to process
            provider: API provider to use
            model: Model to use
            system_prompt: Optional system prompt
            **kwargs: Additional arguments for generate_response
        
        Returns:
            List of APIResponse objects
        """
        results = []
        for i, prompt in enumerate(prompts):
            logger.info(f"Processing prompt {i+1}/{len(prompts)}")
            response = self.generate_response(
                prompt=prompt,
                provider=provider,
                model=model,
                system_prompt=system_prompt,
                **kwargs
            )
            results.append(response)
            
            # Add small delay between requests to avoid rate limiting
            if i < len(prompts) - 1:
                time.sleep(0.5)
        
        return results


# Singleton instance for easy access
api_handler = APIHandler()

# Convenience function for quick access
def generate_ai_response(
    prompt: str,
    provider: str = "openai",
    model: str = "gpt-3.5-turbo",
    **kwargs
) -> str:
    """
    Convenience function to generate AI response.
    
    Args:
        prompt: The user prompt
        provider: API provider name
        model: Model name
        **kwargs: Additional arguments for generate_response
    
    Returns:
        Generated response text or error message
    """
    response = api_handler.generate_response(
        prompt=prompt,
        provider=provider,
        model=model,
        **kwargs
    )
    
    if response.success:
        return response.data
    else:
        return f"Error: {response.error}"


if __name__ == "__main__":
    # Example usage
    handler = APIHandler()
    
    # Test with a simple prompt
    test_response = handler.generate_response(
        prompt="What is the capital of France?",
        provider=APIProvider.OPENAI,
        model=APIModel.GPT35_TURBO.value,
        max_tokens=50
    )
    
    if test_response.success:
        print(f"Response: {test_response.data}")
        print(f"Tokens used: {test_response.tokens_used}")
        print(f"Latency: {test_response.latency:.2f}s")
    else:
        print(f"Error: {test_response.error}")
    
    # Print available providers
    print(f"\nAvailable providers: {handler.get_available_providers()}")