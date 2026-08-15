"""
Health check utilities for monitoring system dependencies and service status.
Validates that all required components are functioning properly.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
import requests
from core.exceptions import HealthCheckError
from core.logger import get_logger
import concurrent.futures

logger = get_logger(__name__)


class HealthCheck:
    """
    Comprehensive health check for all system dependencies.
    Validates configuration, external services, and system resources.
    """
    
    @staticmethod
    def check_python_version() -> Tuple[bool, str]:
        """
        Check if Python version meets requirements.
        
        Returns:
            Tuple of (is_healthy, message)
        """
        required_version = (3, 8)
        current_version = sys.version_info[:2]
        
        if current_version >= required_version:
            return True, f"[okay] Python {current_version[0]}.{current_version[1]}"
        else:
            return False, f"[wrong] Python {current_version[0]}.{current_version[1]} (requires >= {required_version[0]}.{required_version[1]})"
    
    @staticmethod
    def check_ffmpeg() -> Tuple[bool, str]:
        """
        Check if FFmpeg is installed and accessible.
        
        Returns:
            Tuple of (is_healthy, message)
        """
        try:
            import subprocess
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Extract version from first line
                version_line = result.stdout.split('\n')[0]
                return True, f"[okay] FFmpeg installed: {version_line}"
            else:
                return False, "[wrong] FFmpeg found but returned error"
                
        except FileNotFoundError:
            return False, "[wrong] FFmpeg not found in PATH"
        except Exception as e:
            return False, f"[wrong] FFmpeg check failed: {str(e)}"
    
    @staticmethod
    def check_disk_space(required_gb: float = 1.0) -> Tuple[bool, str]:
        """
        Check if sufficient disk space is available.
        
        Args:
            required_gb: Required disk space in GB
            
        Returns:
            Tuple of (is_healthy, message)
        """
        try:
            import shutil
            stat = shutil.disk_usage(Path.cwd())
            
            free_gb = stat.free / (1024 ** 3)
            
            if free_gb >= required_gb:
                return True, f"[okay] Disk space: {free_gb:.2f} GB available"
            else:
                return False, f"[warning]  Low disk space: {free_gb:.2f} GB (recommended: {required_gb} GB)"
                
        except Exception as e:
            return False, f"[wrong] Disk space check failed: {str(e)}"
    
    @staticmethod
    def check_directories() -> Tuple[bool, str]:
        """
        Check if required directories exist and are writable.
        
        Returns:
            Tuple of (is_healthy, message)
        """
        required_dirs = ['downloads', 'logs', 'vector_db']
        issues = []
        
        for dir_name in required_dirs:
            dir_path = Path(dir_name)
            
            try:
                # Try to create directory if it doesn't exist
                dir_path.mkdir(parents=True, exist_ok=True)
                
                # Test write permission
                test_file = dir_path / '.health_check_test'
                test_file.write_text('test')
                test_file.unlink()
                
            except Exception as e:
                issues.append(f"{dir_name}: {str(e)}")
        
        if not issues:
            return True, f"[okay] Directories: {', '.join(required_dirs)} are writable"
        else:
            return False, f"[wrong] Directory issues: {'; '.join(issues)}"
    
    @staticmethod
    def check_environment_variables() -> Tuple[bool, str]:
        """
        Check if required environment variables are set.
        
        Returns:
            Tuple of (is_healthy, message)
        """
        required_vars = ['MISTRAL_API_KEY']
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if not missing_vars:
            optional_set = []
            if os.getenv('SARVAM_API_KEY'):
                optional_set.append('SARVAM_API_KEY')
            
            msg = "[okay] Required environment variables set"
            if optional_set:
                msg += f" (+ optional: {', '.join(optional_set)})"
            return True, msg
        else:
            return False, f"[wrong] Missing environment variables: {', '.join(missing_vars)}"
    
    @staticmethod
    def check_mistral_api() -> Tuple[bool, str]:
        """
        Check Mistral API connectivity and authentication.
        
        Returns:
            Tuple of (is_healthy, message)
        """
        api_key = os.getenv('MISTRAL_API_KEY')
        
        if not api_key:
            return False, "[wrong] MISTRAL_API_KEY not set"
        
        try:
            from langchain_mistralai import ChatMistralAI
            
            # Try to initialize the client
            llm = ChatMistralAI(
                model="mistral-small-latest",
                mistral_api_key=api_key,
                timeout=10
            )
            
            # Make a minimal test call
            response = llm.invoke("test")
            
            return True, "[okay] Mistral API: Connected and authenticated"
            
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "unauthorized" in error_msg.lower():
                return False, "[wrong] Mistral API: Invalid API key"
            elif "429" in error_msg or "rate limit" in error_msg.lower():
                return False, "[warning]  Mistral API: Rate limit reached"
            elif "timeout" in error_msg.lower():
                return False, "[warning]  Mistral API: Connection timeout"
            else:
                return False, f"[wrong] Mistral API: {error_msg[:100]}"
    
    @staticmethod
    def check_sarvam_api() -> Tuple[bool, str]:
        """
        Check Sarvam API connectivity and authentication.
        
        Returns:
            Tuple of (is_healthy, message)
        """
        api_key = os.getenv('SARVAM_API_KEY')
        
        if not api_key:
            return True, "  Sarvam API: Not configured (optional for English-only)"
        
        try:
            # Simple connectivity test
            headers = {"api-subscription-key": api_key}
            response = requests.get(
                "https://api.sarvam.ai/",
                headers=headers,
                timeout=10
            )
            
            # Even if endpoint doesn't exist, we check authentication
            if response.status_code == 401:
                return False, "[wrong] Sarvam API: Invalid API key"
            else:
                return True, "[okay] Sarvam API: API key configured"
                
        except requests.exceptions.Timeout:
            return False, "[warning]  Sarvam API: Connection timeout"
        except requests.exceptions.ConnectionError:
            return False, "[warning]  Sarvam API: Cannot connect"
        except Exception as e:
            return False, f"[wrong] Sarvam API: {str(e)[:100]}"
    
    @staticmethod
    def check_whisper_model() -> Tuple[bool, str]:
        """
        Check if OpenAI Whisper can be initialized.
        
        Returns:
            Tuple of (is_healthy, message)
        """
        try:
            import whisper
            model_name = os.getenv('WHISPER_MODEL', 'small')
            
            # Check if model name is valid for openai-whisper
            valid_models = [
                "tiny", "tiny.en", "base", "base.en", "small", "small.en",
                "medium", "medium.en", "large-v1", "large-v2", "large-v3", "large"
            ]
            
            if model_name not in valid_models:
                return False, f"[wrong] Whisper: Invalid model '{model_name}'. Valid: {', '.join(valid_models)}"
            
            # Model will be downloaded on first use, so just verify package is available
            return True, f"[okay] Whisper: openai-whisper ready with model '{model_name}'"
            
        except ImportError:
            return False, "[wrong] Whisper: openai-whisper package not installed"
        except Exception as e:
            return False, f"[wrong] Whisper: {str(e)[:100]}"
    
    @staticmethod
    def check_embedding_model() -> Tuple[bool, str]:
        """
        Check if embedding model can be initialized.
        
        Returns:
            Tuple of (is_healthy, message)
        """
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
            
            model_name = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
            
            # Try to initialize (this will download model if needed)
            embeddings = HuggingFaceEmbeddings(
                model_name=model_name,
                model_kwargs={'device': 'cpu'}
            )
            
            # Test embedding generation
            test_embedding = embeddings.embed_query("test")
            
            if test_embedding and len(test_embedding) > 0:
                return True, f"[okay] Embeddings: Model '{model_name}' ready"
            else:
                return False, "[wrong] Embeddings: Model returned invalid output"
                
        except ImportError:
            return False, "[wrong] Embeddings: Required packages not installed"
        except Exception as e:
            return False, f"[wrong] Embeddings: {str(e)[:100]}"
    
    @staticmethod
    def check_vector_store() -> Tuple[bool, str]:
        """
        Check if vector store can be initialized.
        
        Returns:
            Tuple of (is_healthy, message)
        """
        try:
            import chromadb
            from pathlib import Path
            
            db_dir = os.getenv('VECTOR_DB_DIR', 'vector_db')
            db_path = Path(db_dir)
            
            # Ensure directory exists
            db_path.mkdir(parents=True, exist_ok=True)
            
            # Try to initialize client
            client = chromadb.PersistentClient(path=str(db_path))
            
            return True, f"[okay] Vector Store: ChromaDB accessible at '{db_dir}'"
            
        except ImportError:
            return False, "[wrong] Vector Store: ChromaDB not installed"
        except Exception as e:
            return False, f"[wrong] Vector Store: {str(e)[:100]}"
    
    @staticmethod
    def run_all_checks(skip_api_checks: bool = False) -> Dict[str, any]:
        """
        Run all health checks and return comprehensive report.
        
        Args:
            skip_api_checks: If True, skip external API checks (useful for offline testing)
            
        Returns:
            Dictionary with health check results
        """
        logger.info("Starting health check...")
        
        checks = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "overall_status": "healthy",
            "warnings": [],
            "errors": []
        }
        
        # Define all checks
        all_checks = [
            ("python_version", HealthCheck.check_python_version),
            ("ffmpeg", HealthCheck.check_ffmpeg),
            ("disk_space", HealthCheck.check_disk_space),
            ("directories", HealthCheck.check_directories),
            ("environment_variables", HealthCheck.check_environment_variables),
            ("whisper_model", HealthCheck.check_whisper_model),
            ("embedding_model", HealthCheck.check_embedding_model),
            ("vector_store", HealthCheck.check_vector_store),
        ]
        
        # Add API checks if not skipped
        if not skip_api_checks:
            all_checks.extend([
                ("mistral_api", HealthCheck.check_mistral_api),
                ("sarvam_api", HealthCheck.check_sarvam_api),
            ])
        
        # Helper to run potentially slow checks with a timeout so startup doesn't hang
        def run_check_with_timeout(fn, timeout: int = 10):
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                    fut = ex.submit(fn)
                    return fut.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                return False, f"[warning] Health check timed out after {timeout}s"
            except Exception as e:
                return False, f"[wrong] Check raised exception: {str(e)[:200]}"

        # Run all checks
        for check_name, check_func in all_checks:
            try:
                # Use shorter timeout for quick checks, longer for model checks
                if check_name in ("whisper_model", "embedding_model", "vector_store"):
                    is_healthy, message = run_check_with_timeout(check_func, timeout=15)
                else:
                    is_healthy, message = run_check_with_timeout(check_func, timeout=8)

                checks["checks"][check_name] = {
                    "status": "pass" if is_healthy else "fail",
                    "message": message
                }

                if not is_healthy:
                    if "[warning]" in message or "timed out" in message:
                        checks["warnings"].append(f"{check_name}: {message}")
                    else:
                        checks["errors"].append(f"{check_name}: {message}")
                        checks["overall_status"] = "unhealthy"

            except Exception as e:
                logger.error(f"Health check '{check_name}' raised exception: {str(e)}")
                checks["checks"][check_name] = {
                    "status": "error",
                    "message": f"[wrong] Check failed: {str(e)}"
                }
                checks["errors"].append(f"{check_name}: {str(e)}")
                checks["overall_status"] = "unhealthy"
        
        # Log summary
        if checks["overall_status"] == "healthy":
            logger.info("[okay] Health check passed - All systems operational")
        else:
            logger.error(f"[warning] Health check failed - {len(checks['errors'])} error(s)")
        
        if checks["warnings"]:
            logger.warning(f"[warning]  Health check warnings: {len(checks['warnings'])} warning(s)")
        
        return checks
    
    @staticmethod
    def print_health_report(checks: Dict[str, any]):
        """
        Print a formatted health check report.
        
        Args:
            checks: Health check results dictionary
        """
        print("\n" + "=" * 80)
        print(" AI Video Agent - Health Check Report")
        print("=" * 80)
        print(f"Timestamp: {checks['timestamp']}")
        print(f"Overall Status: {checks['overall_status'].upper()}")
        print("=" * 80 + "\n")
        
        # Print individual checks
        for check_name, result in checks["checks"].items():
            print(f"{check_name:25} {result['message']}")
        
        # Print summary
        print("\n" + "=" * 80)
        
        if checks["errors"]:
            print(f" Errors ({len(checks['errors'])}):")
            for error in checks["errors"]:
                print(f"   - {error}")
            print()
        
        if checks["warnings"]:
            print(f"  Warnings ({len(checks['warnings'])}):")
            for warning in checks["warnings"]:
                print(f"   - {warning}")
            print()
        
        if checks["overall_status"] == "healthy":
            print("[okay] System is ready for operation")
        else:
            print("[wrong] System has issues that need to be resolved")
        
        print("=" * 80 + "\n")


def perform_health_check(skip_api_checks: bool = False, print_report: bool = True) -> bool:
    """
    Convenience function to perform health check.
    
    Args:
        skip_api_checks: Skip external API connectivity checks
        print_report: Print formatted report to console
        
    Returns:
        True if system is healthy, False otherwise
    """
    checks = HealthCheck.run_all_checks(skip_api_checks=skip_api_checks)
    
    if print_report:
        HealthCheck.print_health_report(checks)
    
    return checks["overall_status"] == "healthy"


