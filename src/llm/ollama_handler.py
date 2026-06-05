"""Ollama LLM handler for Triathlon Coach AI"""
import httpx
import json
import logging
import time
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class OllamaHandler:
    """Handler for Ollama local LLM inference"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama2:7b",
        timeout: int = 120
    ):
        """
        Initialize Ollama handler
        
        Args:
            base_url: Ollama server base URL
            model: Model name to use
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        self.client = httpx.Client(
            timeout=httpx.Timeout(
                connect=10.0,
                read=timeout,
                write=timeout,
                pool=10.0
            )
        )
    
    def health_check(self) -> bool:
        """Check if Ollama is running and responsive"""
        try:
            response = self.client.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False
    
    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate text from LLM
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt to prepend
        
        Returns:
            Generated text
        """
        try:
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            response = self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "stream": False
                }
            )
            response.raise_for_status()
            
            result = response.json()
            logger.debug(f"LLM generated {len(result['response'])} characters")
            return result["response"]
            
        except httpx.HTTPError as e:
            logger.error(f"Ollama API error: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Ollama response: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in generate: {e}")
            raise
    
    def generate_json(
        self,
        prompt: str,
        retries: int = 3,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate JSON response from LLM
        
        Args:
            prompt: Input prompt
            retries: Number of retry attempts
            system_prompt: Optional system prompt
        
        Returns:
            Parsed JSON response
        """
        json_instruction = "Respond with valid JSON only, no markdown formatting."
        full_prompt = f"{prompt}\n\n{json_instruction}"
        
        for attempt in range(retries):
            try:
                response = self.generate(
                    full_prompt,
                    temperature=0.5,  # Lower temp for consistency
                    system_prompt=system_prompt
                )
                
                # Clean up response
                json_str = response.strip()
                
                # Remove markdown code blocks if present
                if json_str.startswith("```json"):
                    json_str = json_str[7:]
                if json_str.startswith("```"):
                    json_str = json_str[3:]
                if json_str.endswith("```"):
                    json_str = json_str[:-3]
                
                json_str = json_str.strip()
                
                # Parse and return
                parsed = json.loads(json_str)
                logger.debug(f"Successfully parsed JSON response (attempt {attempt + 1})")
                return parsed
                
            except json.JSONDecodeError as e:
                if attempt == retries - 1:
                    logger.error(f"Failed to parse JSON after {retries} attempts: {e}")
                    raise
                logger.warning(f"JSON parse attempt {attempt + 1} failed, retrying...")
                time.sleep(0.5)  # Wait before retry
        
        raise ValueError("Failed to generate valid JSON")
    
    def stream(
        self,
        prompt: str,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ):
        """
        Stream text generation (generator)
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            system_prompt: Optional system prompt
        
        Yields:
            Text chunks as they're generated
        """
        try:
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            with self.client.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "temperature": temperature,
                    "stream": True
                }
            ) as response:
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            logger.error(f"Error in stream: {e}")
            raise
    
    def list_models(self) -> list:
        """Get list of available models"""
        try:
            response = self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            models = [model["name"] for model in data.get("models", [])]
            logger.info(f"Available models: {models}")
            return models
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
    
    def pull_model(self, model: str) -> bool:
        """
        Pull/download a model
        
        Args:
            model: Model name
        
        Returns:
            True if successful
        """
        try:
            response = self.client.post(
                f"{self.base_url}/api/pull",
                json={"name": model},
                timeout=None  # Allow unlimited time for downloads
            )
            response.raise_for_status()
            logger.info(f"✓ Successfully pulled model {model}")
            return True
        except Exception as e:
            logger.error(f"Error pulling model {model}: {e}")
            return False
    
    def __del__(self):
        """Cleanup"""
        if self.client:
            self.client.close()