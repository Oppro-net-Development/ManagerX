    # Copyright (c) 2025 OPPRO.NET Network
"""
Update Checker Module for ManagerX
===================================

Handles version checking and update notifications for the bot.
Compares current version against remote version to detect available updates.

Version Format: MAJOR.MINOR.PATCH[-TYPE]
  - TYPE: dev, beta, alpha, or stable (default)
  - Example: 1.7.2-alpha, 2.0.0, 1.5.1-beta
"""

import re
import asyncio
import aiohttp
from typing import Optional, Tuple
from colorama import Fore, Style

try:
    from log import logger, C
except ImportError:
    # Fallback if logger is not available
    import logging
    logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

class UpdateCheckerConfig:
    """
    Configuration for the Update Checker.
    
    Contains all URLs and settings needed for version checking.
    """
    # GitHub repository
    GITHUB_REPO = "https://github.com/Oppro-net-Development/ManagerX"
    
    # Raw GitHub URL for version file
    # Points to the version.txt file on the main branch
    VERSION_URL = "https://raw.githubusercontent.com/Oppro-net-Development/ManagerX/main/config/version.txt"
    
    # Timeout for version check requests (in seconds)
    TIMEOUT = 10


# =============================================================================
# Version Checker Class
# =============================================================================

class VersionChecker:
    """
    Handles version parsing and update checking for ManagerX.
    
    Supports semantic versioning with optional pre-release type identifiers.
    Automatically detects when updates are available and logs appropriate messages.
    
    Attributes
    ----------
    GITHUB_REPO : str
        Repository URL for update notifications
    VERSION_URL : str
        URL to the version file on GitHub
    TIMEOUT : int
        Timeout for requests in seconds
    
    Examples
    --------
    >>> current = "1.7.2-alpha"
    >>> latest = await VersionChecker.check_update(current, UpdateCheckerConfig.VERSION_URL)
    >>> print(f"Latest version: {latest}")
    """
    
    GITHUB_REPO = UpdateCheckerConfig.GITHUB_REPO
    VERSION_URL = UpdateCheckerConfig.VERSION_URL
    TIMEOUT = UpdateCheckerConfig.TIMEOUT
    
    @staticmethod
    def parse_version(version_str: str) -> Tuple[int, int, int, str]:
        """
        Parse version string into components.
        
        Parses semantic versioning with optional pre-release type.
        Format: MAJOR.MINOR.PATCH[-TYPE]
        
        Parameters
        ----------
        version_str : str
            Version string to parse (e.g., "1.7.2-alpha")
        
        Returns
        -------
        tuple
            Tuple of (major, minor, patch, type)
            - major : int
            - minor : int
            - patch : int
            - type : str - 'dev', 'beta', 'alpha', or 'stable' (default)
        
        Examples
        --------
        >>> VersionChecker.parse_version("1.7.2-alpha")
        (1, 7, 2, 'alpha')
        
        >>> VersionChecker.parse_version("2.0.0")
        (2, 0, 0, 'stable')
        """
        match = re.match(r"(\d+)\.(\d+)\.(\d+)(?:[-_]?(dev|beta|alpha))?", version_str)
        if match:
            major, minor, patch, vtype = match.groups()
            return int(major), int(minor), int(patch), vtype or "stable"
        return 0, 0, 0, "unknown"
    
    @staticmethod
    async def check_update(current_version: str, version_url: str) -> Optional[str]:
        """
        Check for available updates by comparing current and latest versions.
        
        Fetches the latest version from a remote URL and compares it with
        the current version. Logs appropriate messages based on comparison:
        
        - Up to date: Success message
        - Dev build: Info message
        - Pre-release: Warning message
        - Update available: Yellow alert with download link
        - Error: Error message with details
        
        Parameters
        ----------
        current_version : str
            Current bot version (e.g., "1.7.2-alpha")
        version_url : str
            URL pointing to the latest version number
            Should return plain text with only the version number
        
        Returns
        -------
        Optional[str]
            Latest version string if successfully retrieved, None if error occurred
        
        Raises
        ------
        None
            All exceptions are caught and logged
        
        Examples
        --------
        >>> url = "https://raw.githubusercontent.com/.../version.txt"
        >>> latest = await VersionChecker.check_update("1.7.2", url)
        >>> if latest and latest > "1.7.2":
        ...     print("Update available!")
        
        Notes
        -----
        Network timeouts are set to 10 seconds. Failed connections are
        logged but do not prevent bot startup.
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(version_url, timeout=aiohttp.ClientTimeout(total=VersionChecker.TIMEOUT)) as resp:
                    if resp.status != 200:
                        logger.error(C.DEV.VER, f"Version check failed (HTTP {resp.status})")
                        return None
                    
                    latest_version = (await resp.text()).strip()
                    if not latest_version:
                        logger.error(C.DEV.UPDATE, "Empty response from version server")
                        return None
                    
                    # Parse versions for comparison
                    current = VersionChecker.parse_version(current_version)
                    latest = VersionChecker.parse_version(latest_version)
                    
                    # Compare major, minor, patch (ignore pre-release type)
                    current_core = current[:3]
                    latest_core = latest[:3]
                    
                    # Version is up to date
                    if current_core == latest_core and current[3] == latest[3]:
                        logger.success(C.DEV.VER, f"Running latest version: {current_version}")
                    
                    # Dev build newer than public release
                    elif current_core > latest_core:
                        logger.info(
                            C.DEV.VER,
                            f"Dev build detected ({current_version}) - newer than public release ({latest_version})"
                        )
                    
                    # Pre-release version
                    elif current_core == latest_core and current[3] in ("dev", "beta", "alpha"):
                        logger.warn(
                            C.DEV.VER,
                            f"Pre-release version ({current_version}) - latest stable: {latest_version}"
                        )
                    
                    # Update available
                    else:
                        print(
                            f"[{Fore.YELLOW}UPDATE AVAILABLE{Style.RESET_ALL}] "
                            f"Current: {current_version} → Latest: {latest_version}\n"
                            f"        Download: {Fore.CYAN}{VersionChecker.GITHUB_REPO}{Style.RESET_ALL}"
                        )
                    
                    return latest_version
        
        except aiohttp.ClientConnectorError:
            logger.error(C.DEV.UPDATE, "Could not connect to GitHub (network issue)")
        except asyncio.TimeoutError:
            logger.error(C.DEV.UPDATE, "Connection to version server timed out")
        except Exception as e:
            logger.error(C.DEV.UPDATE, f"Unexpected error: {e}")
        
        return None


__all__ = ["VersionChecker", "UpdateCheckerConfig"]
