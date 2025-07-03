"""
Tesseract Configuration Module
Automatically detects and configures Tesseract paths
"""

import os
import json
import platform
import subprocess
import pytesseract
from pathlib import Path

class TesseractConfig:
    def __init__(self):
        self.system = platform.system().lower()
        if self.system == 'windows':
            self.system = 'windows'
        elif self.system == 'linux':
            self.system = 'linux'
        elif self.system == 'darwin':
            self.system = 'darwin'
        else:
            self.system = 'linux'  # Default fallback
        
        # Load paths configuration
        config_path = Path(__file__).parent.parent / 'config' / 'tesseract_paths.json'
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.tesseract_path = None
        self.tessdata_path = None
        
    def find_tesseract(self):
        """Find Tesseract executable on the system"""
        # First, check if tesseract is in PATH
        if self._check_command_exists('tesseract'):
            self.tesseract_path = 'tesseract'
            return True
        
        # Check default path for the OS
        default_path = self.config[self.system]['default']
        if self.system == 'windows':
            # Expand environment variables
            default_path = os.path.expandvars(default_path)
        
        if os.path.exists(default_path):
            self.tesseract_path = default_path
            return True
        
        # Check alternative paths
        for path in self.config[self.system]['alternative_paths']:
            if self.system == 'windows':
                path = os.path.expandvars(path)
            
            if os.path.exists(path):
                self.tesseract_path = path
                return True
        
        return False
    
    def configure(self):
        """Configure Tesseract for the system"""
        if not self.find_tesseract():
            raise TesseractNotFoundError(
                f"Tesseract not found on {self.system}. "
                f"Please install it using the instructions below:\n"
                f"{self.get_install_instructions()}"
            )
        
        # Set the path in pytesseract
        if self.tesseract_path != 'tesseract':  # Only set if not in PATH
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
        
        # Verify installation
        try:
            version = pytesseract.get_tesseract_version()
            print(f"✓ Tesseract found: {self.tesseract_path}")
            print(f"  Version: {version}")
            
            # Check languages
            languages = pytesseract.get_languages()
            print(f"  Languages: {', '.join(languages)}")
            
            # Check for required languages
            required = self.config['language_data']['required']
            missing = [lang for lang in required if lang not in languages]
            
            if missing:
                print(f"  ⚠ Missing required languages: {', '.join(missing)}")
            
            return True
            
        except Exception as e:
            raise TesseractConfigError(f"Failed to configure Tesseract: {str(e)}")
    
    def get_install_instructions(self):
        """Get installation instructions for the current OS"""
        instructions = []
        
        if self.system == 'windows':
            instructions.append("Windows Installation:")
            instructions.append(f"1. Download: {self.config['windows']['installer_url']}")
            instructions.append(f"2. Install to: {self.config['windows']['default']}")
            instructions.append("3. Restart your terminal/IDE")
            
        elif self.system == 'linux':
            instructions.append("Linux Installation:")
            commands = self.config['linux']['install_commands']
            
            # Detect Linux distribution
            distro = self._detect_linux_distro()
            if distro in commands:
                instructions.append(f"Run: {commands[distro]}")
            else:
                instructions.append("Ubuntu/Debian: " + commands['ubuntu'])
                instructions.append("Fedora: " + commands['fedora'])
                instructions.append("Arch: " + commands['arch'])
                
        elif self.system == 'darwin':
            instructions.append("macOS Installation:")
            instructions.append("Using Homebrew:")
            instructions.append(f"  {self.config['darwin']['install_commands']['homebrew']}")
            instructions.append(f"  {self.config['darwin']['install_commands']['homebrew_languages']}")
            
        return '\n'.join(instructions)
    
    def get_tessdata_path(self):
        """Get the tessdata directory path"""
        if self.tessdata_path:
            return self.tessdata_path
        
        # Check environment variable
        env_path = os.environ.get('TESSDATA_PREFIX')
        if env_path and os.path.exists(env_path):
            self.tessdata_path = env_path
            return env_path
        
        # Use default for OS
        default_path = self.config['language_data']['paths'][self.system]
        if os.path.exists(default_path):
            self.tessdata_path = default_path
            return default_path
        
        # Try to find it relative to tesseract executable
        if self.tesseract_path and self.tesseract_path != 'tesseract':
            tessdata = os.path.join(os.path.dirname(self.tesseract_path), 'tessdata')
            if os.path.exists(tessdata):
                self.tessdata_path = tessdata
                return tessdata
        
        return None
    
    def install_language(self, language_code):
        """Download and install a language pack"""
        tessdata_path = self.get_tessdata_path()
        if not tessdata_path:
            raise TesseractConfigError("Cannot find tessdata directory")
        
        # Check if already installed
        lang_file = os.path.join(tessdata_path, f"{language_code}.traineddata")
        if os.path.exists(lang_file):
            print(f"Language '{language_code}' already installed")
            return True
        
        # Download language file
        url = f"https://github.com/tesseract-ocr/tessdata/raw/main/{language_code}.traineddata"
        print(f"Downloading {language_code} language pack...")
        
        try:
            import urllib.request
            urllib.request.urlretrieve(url, lang_file)
            print(f"✓ Installed {language_code} language pack")
            return True
        except Exception as e:
            print(f"✗ Failed to download {language_code}: {str(e)}")
            return False
    
    def _check_command_exists(self, command):
        """Check if a command exists in PATH"""
        try:
            subprocess.run([command, '--version'], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _detect_linux_distro(self):
        """Detect Linux distribution"""
        try:
            with open('/etc/os-release', 'r') as f:
                content = f.read().lower()
                if 'ubuntu' in content or 'debian' in content:
                    return 'ubuntu'
                elif 'fedora' in content:
                    return 'fedora'
                elif 'centos' in content or 'rhel' in content:
                    return 'centos'
                elif 'arch' in content:
                    return 'arch'
        except:
            pass
        return 'ubuntu'  # Default

class TesseractNotFoundError(Exception):
    """Raised when Tesseract is not found on the system"""
    pass

class TesseractConfigError(Exception):
    """Raised when Tesseract configuration fails"""
    pass

# Singleton instance
_config_instance = None

def configure_tesseract():
    """Configure Tesseract for the current system"""
    global _config_instance
    
    if _config_instance is None:
        _config_instance = TesseractConfig()
        _config_instance.configure()
    
    return _config_instance

def get_tesseract_path():
    """Get the configured Tesseract path"""
    config = configure_tesseract()
    return config.tesseract_path

def get_tessdata_path():
    """Get the tessdata directory path"""
    config = configure_tesseract()
    return config.get_tessdata_path()

def install_language_pack(language_code):
    """Install a Tesseract language pack"""
    config = configure_tesseract()
    return config.install_language(language_code)

# Auto-configure when module is imported
if __name__ != "__main__":
    try:
        configure_tesseract()
    except Exception as e:
        print(f"Warning: Tesseract auto-configuration failed: {str(e)}")
        print("Please configure manually or run the installer.")