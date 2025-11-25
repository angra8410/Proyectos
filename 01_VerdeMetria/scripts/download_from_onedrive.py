#!/usr/bin/env python3
"""
OneDrive Download Helper

Provides two methods to download files from OneDrive:
1. Public link download (no auth required)
2. Microsoft Graph API download (requires app credentials)

Usage:
    from download_from_onedrive import download_public_onedrive, download_graph_share
    
    # Public link
    download_public_onedrive("https://1drv.ms/...", "output.csv")
    
    # Graph API
    download_graph_share(
        share_url="https://onedrive.live.com/...",
        tenant_id="your-tenant-id",
        client_id="your-client-id", 
        client_secret="your-client-secret",
        dest="output.csv"
    )
"""

import os
import re
import base64
import logging
import requests
from urllib.parse import urlparse, unquote

logger = logging.getLogger(__name__)


def download_public_onedrive(public_link: str, dest: str, timeout: int = 120) -> bool:
    """
    Download a file from a public OneDrive/SharePoint link.
    
    Converts share links to direct download URLs using OneDrive's redirection.
    
    Args:
        public_link: Public OneDrive share link (https://1drv.ms/... or similar)
        dest: Destination file path
        timeout: Request timeout in seconds
        
    Returns:
        bool: True if download succeeded, False otherwise
    """
    try:
        # Convert 1drv.ms short links to download URL
        # OneDrive public links can be converted by changing 'redir' to 'download'
        # or by using the sharing API trick
        
        if "1drv.ms" in public_link or "sharepoint.com" in public_link:
            # Try direct download approach - follow redirects
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            # Method 1: Direct redirect following
            response = requests.get(
                public_link, 
                headers=headers, 
                allow_redirects=True,
                timeout=timeout,
                stream=True
            )
            
            # Check if we got a download or need to modify URL
            content_type = response.headers.get("Content-Type", "")
            
            if "text/html" in content_type:
                # We got HTML page, try to extract download URL
                # or convert link format
                download_url = _convert_to_download_url(public_link)
                if download_url:
                    response = requests.get(
                        download_url,
                        headers=headers,
                        allow_redirects=True,
                        timeout=timeout,
                        stream=True
                    )
            
            response.raise_for_status()
            
            # Ensure parent directory exists
            os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
            
            # Write file
            with open(dest, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"Downloaded {dest} from public link")
            return True
            
    except requests.RequestException as e:
        logger.warning(f"Public download failed: {e}")
    except IOError as e:
        logger.error(f"File write error: {e}")
    
    return False


def _convert_to_download_url(share_link: str) -> str:
    """
    Convert a OneDrive share link to a direct download URL.
    
    Uses the base64 encoding trick for OneDrive sharing links.
    """
    try:
        # Method: Base64 encode the share URL and create API URL
        # This works for personal OneDrive links
        
        # Encode the sharing URL
        encoded = base64.urlsafe_b64encode(share_link.encode()).decode()
        # Remove padding and prefix with 'u!'
        encoded = "u!" + encoded.rstrip("=")
        
        # Construct the download URL
        download_url = f"https://api.onedrive.com/v1.0/shares/{encoded}/root/content"
        
        return download_url
    except Exception:
        return None


def download_graph_share(
    share_url: str,
    tenant_id: str,
    client_id: str,
    client_secret: str,
    dest: str,
    timeout: int = 120
) -> bool:
    """
    Download a file from OneDrive using Microsoft Graph API.
    
    Requires Azure AD app registration with Files.Read.All or Sites.Read.All permissions.
    
    Args:
        share_url: OneDrive/SharePoint sharing URL or item URL
        tenant_id: Azure AD tenant ID
        client_id: Azure AD application (client) ID
        client_secret: Azure AD client secret
        dest: Destination file path
        timeout: Request timeout in seconds
        
    Returns:
        bool: True if download succeeded, False otherwise
    """
    try:
        # Get access token
        token = _get_graph_token(tenant_id, client_id, client_secret)
        if not token:
            logger.error("Failed to obtain Graph API token")
            return False
        
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "VerdeMetria-Downloader/1.0"
        }
        
        # Convert share URL to encoded format for Graph API
        encoded_url = base64.urlsafe_b64encode(share_url.encode()).decode()
        encoded_url = "u!" + encoded_url.rstrip("=")
        
        # Get the sharing item info
        graph_url = f"https://graph.microsoft.com/v1.0/shares/{encoded_url}/driveItem"
        
        response = requests.get(graph_url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        item_info = response.json()
        
        # Get download URL from @microsoft.graph.downloadUrl or use content endpoint
        download_url = item_info.get("@microsoft.graph.downloadUrl")
        
        if not download_url:
            # Use the content endpoint
            drive_id = item_info.get("parentReference", {}).get("driveId")
            item_id = item_info.get("id")
            if drive_id and item_id:
                download_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}/content"
        
        if not download_url:
            logger.error("Could not determine download URL from Graph API")
            return False
        
        # Download the file
        # Note: @microsoft.graph.downloadUrl doesn't need auth header
        if "@microsoft.graph.downloadUrl" in str(download_url):
            dl_response = requests.get(download_url, timeout=timeout, stream=True)
        else:
            dl_response = requests.get(download_url, headers=headers, timeout=timeout, stream=True)
        
        dl_response.raise_for_status()
        
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
        
        # Write file
        with open(dest, "wb") as f:
            for chunk in dl_response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        logger.info(f"Downloaded {dest} via Graph API")
        return True
        
    except requests.RequestException as e:
        logger.error(f"Graph API download failed: {e}")
    except IOError as e:
        logger.error(f"File write error: {e}")
    
    return False


def _get_graph_token(tenant_id: str, client_id: str, client_secret: str) -> str:
    """
    Get an access token from Azure AD using client credentials flow.
    
    Returns:
        str: Access token or None if failed
    """
    try:
        token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        
        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "https://graph.microsoft.com/.default"
        }
        
        response = requests.post(token_url, data=data, timeout=30)
        response.raise_for_status()
        
        return response.json().get("access_token")
        
    except requests.RequestException as e:
        logger.error(f"Token request failed: {e}")
        return None


def ensure_file_local(
    filepath: str,
    public_url: str = None,
    share_url: str = None,
    tenant_id: str = None,
    client_id: str = None,
    client_secret: str = None,
    force: bool = False
) -> bool:
    """
    Ensure a file exists locally, downloading from OneDrive if needed.
    
    Tries methods in order:
    1. Check if file already exists (unless force=True)
    2. Try public URL download
    3. Try Graph API download (if credentials provided)
    
    Args:
        filepath: Local path where file should exist
        public_url: Optional public OneDrive link
        share_url: Optional OneDrive share URL for Graph API
        tenant_id: Azure AD tenant ID (for Graph API)
        client_id: Azure AD client ID (for Graph API)
        client_secret: Azure AD client secret (for Graph API)
        force: Force re-download even if file exists
        
    Returns:
        bool: True if file exists or was downloaded successfully
    """
    # Check if file already exists
    if not force and os.path.exists(filepath):
        logger.info(f"File already exists: {filepath}")
        return True
    
    # Try public URL first
    if public_url:
        logger.info(f"Trying public URL download for {filepath}")
        if download_public_onedrive(public_url, filepath):
            return True
    
    # Try Graph API
    if share_url and tenant_id and client_id and client_secret:
        logger.info(f"Trying Graph API download for {filepath}")
        if download_graph_share(share_url, tenant_id, client_id, client_secret, filepath):
            return True
    
    logger.warning(f"Could not ensure file exists: {filepath}")
    return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Download files from OneDrive")
    parser.add_argument("--url", required=True, help="OneDrive share URL")
    parser.add_argument("--dest", required=True, help="Destination file path")
    parser.add_argument("--tenant-id", help="Azure AD tenant ID (for Graph API)")
    parser.add_argument("--client-id", help="Azure AD client ID (for Graph API)")
    parser.add_argument("--client-secret", help="Azure AD client secret (for Graph API)")
    parser.add_argument("--test", action="store_true", help="Test mode - verify URL format only")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    if args.test:
        print(f"URL: {args.url}")
        print(f"Dest: {args.dest}")
        converted = _convert_to_download_url(args.url)
        print(f"Converted URL: {converted}")
        print("Test mode - no download performed")
    else:
        success = ensure_file_local(
            filepath=args.dest,
            public_url=args.url,
            share_url=args.url,
            tenant_id=args.tenant_id,
            client_id=args.client_id,
            client_secret=args.client_secret
        )
        
        if success:
            print(f"Successfully downloaded to {args.dest}")
        else:
            print("Download failed")
            exit(1)
