"""
Secure file upload and virus scanning utilities
"""
import os
import hashlib
import tempfile
import subprocess
import logging
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    logger.warning("python-magic not available, file type detection will be limited")

try:
    import yara
    YARA_AVAILABLE = True
except ImportError:
    YARA_AVAILABLE = False
    logger.warning("yara-python not available, advanced malware detection disabled")
from .input_validation import FileUploadValidator, ValidationError

logger = logging.getLogger(__name__)

class VirusScanner:
    """Virus scanning utility using multiple methods"""
    
    def __init__(self):
        self.clamav_available = self._check_clamav()
        self.yara_rules = self._load_yara_rules()
        
    def _check_clamav(self) -> bool:
        """Check if ClamAV is available"""
        try:
            result = subprocess.run(['clamscan', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                logger.info("ClamAV is available for virus scanning")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            pass
        
        logger.warning("ClamAV not available, using alternative scanning methods")
        return False
    
    def _load_yara_rules(self) -> Optional:
        """Load YARA rules for malware detection"""
        if not YARA_AVAILABLE:
            return None
            
        try:
            # Create basic YARA rules for common malware patterns
            rules_content = '''
            rule SuspiciousExecutable {
                meta:
                    description = "Detects suspicious executable patterns"
                strings:
                    $mz = { 4D 5A }  // MZ header
                    $pe = "PE"
                    $exec1 = "CreateProcess"
                    $exec2 = "ShellExecute"
                    $exec3 = "WinExec"
                condition:
                    $mz at 0 and $pe and any of ($exec*)
            }
            
            rule SuspiciousScript {
                meta:
                    description = "Detects suspicious script patterns"
                strings:
                    $js1 = "eval("
                    $js2 = "document.write"
                    $js3 = "window.location"
                    $vbs1 = "CreateObject"
                    $vbs2 = "WScript.Shell"
                    $ps1 = "powershell"
                    $ps2 = "Invoke-Expression"
                condition:
                    any of them
            }
            
            rule EmbeddedExecutable {
                meta:
                    description = "Detects embedded executables in documents"
                strings:
                    $pdf_js = "/JavaScript"
                    $pdf_launch = "/Launch"
                    $office_macro = "Microsoft Office"
                    $zip_exe = { 50 4B 03 04 } // ZIP header followed by executable patterns
                condition:
                    any of them
            }
            '''
            
            import yara
            return yara.compile(source=rules_content)
            
        except Exception as e:
            logger.warning(f"Could not load YARA rules: {e}")
            return None
    
    async def scan_file(self, file_path: str) -> Dict[str, any]:
        """
        Scan file for viruses and malware
        
        Args:
            file_path: Path to file to scan
            
        Returns:
            Dictionary with scan results
        """
        results = {
            "clean": True,
            "threats": [],
            "scan_methods": [],
            "file_info": {}
        }
        
        try:
            # Get file info
            file_stat = os.stat(file_path)
            results["file_info"] = {
                "size": file_stat.st_size,
                "path": file_path
            }
            
            # Method 1: ClamAV scan
            if self.clamav_available:
                clamav_result = await self._scan_with_clamav(file_path)
                results["scan_methods"].append("clamav")
                if not clamav_result["clean"]:
                    results["clean"] = False
                    results["threats"].extend(clamav_result["threats"])
            
            # Method 2: YARA rules scan
            if self.yara_rules:
                yara_result = await self._scan_with_yara(file_path)
                results["scan_methods"].append("yara")
                if not yara_result["clean"]:
                    results["clean"] = False
                    results["threats"].extend(yara_result["threats"])
            
            # Method 3: File type validation
            filetype_result = await self._validate_file_type(file_path)
            results["scan_methods"].append("filetype")
            if not filetype_result["clean"]:
                results["clean"] = False
                results["threats"].extend(filetype_result["threats"])
            
            # Method 4: Content analysis
            content_result = await self._analyze_content(file_path)
            results["scan_methods"].append("content_analysis")
            if not content_result["clean"]:
                results["clean"] = False
                results["threats"].extend(content_result["threats"])
            
        except Exception as e:
            logger.error(f"Error during virus scan: {e}")
            results["clean"] = False
            results["threats"].append(f"Scan error: {str(e)}")
        
        return results
    
    async def _scan_with_clamav(self, file_path: str) -> Dict[str, any]:
        """Scan file with ClamAV"""
        try:
            result = subprocess.run([
                'clamscan', 
                '--no-summary',
                '--infected',
                file_path
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return {"clean": True, "threats": []}
            elif result.returncode == 1:
                # Virus found
                threats = []
                for line in result.stdout.split('\n'):
                    if 'FOUND' in line:
                        threats.append(f"ClamAV: {line.strip()}")
                return {"clean": False, "threats": threats}
            else:
                # Error occurred
                return {"clean": False, "threats": [f"ClamAV error: {result.stderr}"]}
                
        except subprocess.TimeoutExpired:
            return {"clean": False, "threats": ["ClamAV scan timeout"]}
        except Exception as e:
            return {"clean": False, "threats": [f"ClamAV scan error: {str(e)}"]}
    
    async def _scan_with_yara(self, file_path: str) -> Dict[str, any]:
        """Scan file with YARA rules"""
        try:
            matches = self.yara_rules.match(file_path)
            
            if matches:
                threats = [f"YARA: {match.rule}" for match in matches]
                return {"clean": False, "threats": threats}
            else:
                return {"clean": True, "threats": []}
                
        except Exception as e:
            return {"clean": False, "threats": [f"YARA scan error: {str(e)}"]}
    
    async def _validate_file_type(self, file_path: str) -> Dict[str, any]:
        """Validate file type using python-magic (if available)"""
        try:
            if not MAGIC_AVAILABLE:
                # Fallback to file extension validation
                file_ext = Path(file_path).suffix.lower()
                allowed_extensions = ['.pdf', '.txt', '.csv', '.json']
                
                if file_ext not in allowed_extensions:
                    return {
                        "clean": False, 
                        "threats": [f"Disallowed file extension: {file_ext}"]
                    }
                
                # For PDF files, do basic validation
                if file_ext == '.pdf':
                    return await self._validate_pdf_file(file_path)
                
                return {"clean": True, "threats": []}
            
            # Get MIME type using magic
            mime_type = magic.from_file(file_path, mime=True)
            
            # Allowed MIME types
            allowed_types = [
                'application/pdf',
                'text/plain',
                'text/csv',
                'application/json'
            ]
            
            if mime_type not in allowed_types:
                return {
                    "clean": False, 
                    "threats": [f"Disallowed file type: {mime_type}"]
                }
            
            # Additional checks for PDF files
            if mime_type == 'application/pdf':
                return await self._validate_pdf_file(file_path)
            
            return {"clean": True, "threats": []}
            
        except Exception as e:
            return {"clean": False, "threats": [f"File type validation error: {str(e)}"]}
    
    async def _validate_pdf_file(self, file_path: str) -> Dict[str, any]:
        """Additional validation for PDF files"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read(1024)  # Read first 1KB
            
            # Check for PDF header
            if not content.startswith(b'%PDF'):
                return {"clean": False, "threats": ["Invalid PDF header"]}
            
            # Check for suspicious PDF features
            suspicious_patterns = [
                b'/JavaScript',
                b'/JS',
                b'/Launch',
                b'/SubmitForm',
                b'/ImportData',
                b'/GoToE',
                b'/GoToR'
            ]
            
            threats = []
            for pattern in suspicious_patterns:
                if pattern in content:
                    threats.append(f"Suspicious PDF feature: {pattern.decode('utf-8', errors='ignore')}")
            
            if threats:
                return {"clean": False, "threats": threats}
            
            return {"clean": True, "threats": []}
            
        except Exception as e:
            return {"clean": False, "threats": [f"PDF validation error: {str(e)}"]}
    
    async def _analyze_content(self, file_path: str) -> Dict[str, any]:
        """Analyze file content for suspicious patterns"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            threats = []
            
            # Check file size (prevent zip bombs, etc.)
            if len(content) > 50 * 1024 * 1024:  # 50MB
                threats.append("File too large")
            
            # Check for embedded executables
            if b'MZ' in content and b'PE' in content:
                threats.append("Contains embedded executable")
            
            # Check for suspicious URLs
            suspicious_domains = [
                b'bit.ly',
                b'tinyurl.com',
                b'goo.gl',
                b't.co'
            ]
            
            for domain in suspicious_domains:
                if domain in content:
                    threats.append(f"Contains suspicious URL: {domain.decode()}")
            
            # Check for base64 encoded content (potential payload)
            import base64
            import re
            
            # Look for base64 patterns
            b64_pattern = re.compile(rb'[A-Za-z0-9+/]{50,}={0,2}')
            matches = b64_pattern.findall(content)
            
            for match in matches[:5]:  # Check first 5 matches
                try:
                    decoded = base64.b64decode(match)
                    if b'MZ' in decoded or b'<script' in decoded:
                        threats.append("Suspicious base64 encoded content")
                        break
                except:
                    pass
            
            if threats:
                return {"clean": False, "threats": threats}
            
            return {"clean": True, "threats": []}
            
        except Exception as e:
            return {"clean": False, "threats": [f"Content analysis error: {str(e)}"]}

class SecureFileHandler:
    """Secure file handling with validation and scanning"""
    
    def __init__(self):
        self.virus_scanner = VirusScanner()
        self.temp_dir = tempfile.mkdtemp(prefix="trajectory_secure_")
        
    async def process_upload(self, file_content: bytes, filename: str, 
                           content_type: str, user_id: str) -> Dict[str, any]:
        """
        Securely process file upload
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            content_type: MIME type
            user_id: User ID for logging
            
        Returns:
            Dictionary with processing results
        """
        result = {
            "success": False,
            "file_hash": None,
            "temp_path": None,
            "scan_results": None,
            "validation_errors": [],
            "security_warnings": []
        }
        
        try:
            # Step 1: Basic validation
            FileUploadValidator.validate_file_content(file_content, filename, content_type)
            
            # Step 2: Calculate file hash for deduplication and integrity
            file_hash = hashlib.sha256(file_content).hexdigest()
            result["file_hash"] = file_hash
            
            # Step 3: Save to temporary location for scanning
            temp_path = os.path.join(self.temp_dir, f"{file_hash}_{filename}")
            with open(temp_path, 'wb') as f:
                f.write(file_content)
            
            result["temp_path"] = temp_path
            
            # Step 4: Virus scan
            scan_results = await self.virus_scanner.scan_file(temp_path)
            result["scan_results"] = scan_results
            
            if not scan_results["clean"]:
                result["security_warnings"].extend(scan_results["threats"])
                logger.warning(f"File upload blocked for user {user_id}: {scan_results['threats']}")
                return result
            
            # Step 5: Additional security checks
            security_check = await self._additional_security_checks(temp_path, user_id)
            if not security_check["passed"]:
                result["security_warnings"].extend(security_check["warnings"])
                return result
            
            result["success"] = True
            logger.info(f"File upload approved for user {user_id}: {filename} ({file_hash[:8]})")
            
        except ValidationError as e:
            result["validation_errors"].append(str(e))
            logger.warning(f"File validation failed for user {user_id}: {str(e)}")
        except Exception as e:
            result["validation_errors"].append(f"Processing error: {str(e)}")
            logger.error(f"File processing error for user {user_id}: {str(e)}")
        
        return result
    
    async def _additional_security_checks(self, file_path: str, user_id: str) -> Dict[str, any]:
        """Additional security checks"""
        try:
            # Check file permissions
            file_stat = os.stat(file_path)
            if file_stat.st_mode & 0o111:  # Executable bit set
                return {
                    "passed": False,
                    "warnings": ["File has executable permissions"]
                }
            
            # Check for hidden files or system files
            filename = os.path.basename(file_path)
            if filename.startswith('.') or filename.startswith('~'):
                return {
                    "passed": False,
                    "warnings": ["Hidden or system file detected"]
                }
            
            # Rate limiting check (prevent abuse)
            # This would integrate with the rate limiter
            
            return {"passed": True, "warnings": []}
            
        except Exception as e:
            return {
                "passed": False,
                "warnings": [f"Security check error: {str(e)}"]
            }
    
    def cleanup_temp_file(self, temp_path: str) -> None:
        """Safely cleanup temporary file"""
        try:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
                logger.debug(f"Cleaned up temporary file: {temp_path}")
        except Exception as e:
            logger.error(f"Failed to cleanup temp file {temp_path}: {e}")
    
    def __del__(self):
        """Cleanup temporary directory on destruction"""
        try:
            import shutil
            if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except:
            pass

# Global secure file handler instance
secure_file_handler = SecureFileHandler()