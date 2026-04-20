"""
GitHub Handler for BotManager V2.5
Handles GitHub API operations including repository creation, file management, and webhook setup.
"""

import os
import json
import base64
import requests
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GitHubHandler:
    """Handler for GitHub API operations."""
    
    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize GitHub handler with token.
        
        Args:
            github_token: GitHub personal access token. If None, tries to get from environment.
        """
        self.token = github_token or os.getenv('GITHUB_TOKEN')
        if not self.token:
            raise ValueError("GitHub token is required. Set GITHUB_TOKEN environment variable.")
        
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
        
        # Cache for user info
        self._user_info = None
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                     params: Optional[Dict] = None) -> Tuple[bool, Optional[Dict]]:
        """
        Make HTTP request to GitHub API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            data: Request body data
            params: Query parameters
            
        Returns:
            Tuple of (success, response_data)
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                params=params,
                timeout=30
            )
            
            if response.status_code in [200, 201, 204]:
                return True, response.json() if response.content else {}
            else:
                logger.error(f"GitHub API error: {response.status_code} - {response.text}")
                return False, {"error": response.text, "status_code": response.status_code}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            return False, {"error": str(e)}
    
    def get_user_info(self) -> Optional[Dict]:
        """Get authenticated user information."""
        if self._user_info is None:
            success, data = self._make_request("GET", "/user")
            if success:
                self._user_info = data
        return self._user_info
    
    def create_repository(self, name: str, description: str = "", 
                         private: bool = False, auto_init: bool = True,
                         gitignore_template: str = "Python") -> Tuple[bool, Optional[Dict]]:
        """
        Create a new GitHub repository.
        
        Args:
            name: Repository name
            description: Repository description
            private: Whether repository is private
            auto_init: Initialize with README
            gitignore_template: Gitignore template to use
            
        Returns:
            Tuple of (success, repository_data)
        """
        data = {
            "name": name,
            "description": description,
            "private": private,
            "auto_init": auto_init,
            "gitignore_template": gitignore_template
        }
        
        success, response = self._make_request("POST", "/user/repos", data=data)
        
        if success:
            logger.info(f"Created repository: {name}")
            return True, response
        else:
            logger.error(f"Failed to create repository: {name}")
            return False, response
    
    def create_organization_repository(self, org: str, name: str, 
                                      description: str = "", private: bool = False) -> Tuple[bool, Optional[Dict]]:
        """
        Create repository in an organization.
        
        Args:
            org: Organization name
            name: Repository name
            description: Repository description
            private: Whether repository is private
            
        Returns:
            Tuple of (success, repository_data)
        """
        data = {
            "name": name,
            "description": description,
            "private": private,
            "auto_init": True
        }
        
        success, response = self._make_request("POST", f"/orgs/{org}/repos", data=data)
        
        if success:
            logger.info(f"Created repository in {org}: {name}")
            return True, response
        else:
            logger.error(f"Failed to create repository in {org}: {name}")
            return False, response
    
    def get_repository(self, owner: str, repo: str) -> Tuple[bool, Optional[Dict]]:
        """
        Get repository information.
        
        Args:
            owner: Repository owner (user or org)
            repo: Repository name
            
        Returns:
            Tuple of (success, repository_data)
        """
        return self._make_request("GET", f"/repos/{owner}/{repo}")
    
    def delete_repository(self, owner: str, repo: str) -> Tuple[bool, Optional[Dict]]:
        """
        Delete a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Tuple of (success, response_data)
        """
        success, response = self._make_request("DELETE", f"/repos/{owner}/{repo}")
        
        if success:
            logger.info(f"Deleted repository: {owner}/{repo}")
            return True, response
        else:
            logger.error(f"Failed to delete repository: {owner}/{repo}")
            return False, response
    
    def create_file(self, owner: str, repo: str, path: str, 
                   content: str, message: str = "", branch: str = "main") -> Tuple[bool, Optional[Dict]]:
        """
        Create or update a file in repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: File path in repository
            content: File content
            message: Commit message
            branch: Target branch
            
        Returns:
            Tuple of (success, response_data)
        """
        # Encode content to base64
        encoded_content = base64.b64encode(content.encode()).decode()
        
        data = {
            "message": message or f"Add {path}",
            "content": encoded_content,
            "branch": branch
        }
        
        success, response = self._make_request("PUT", f"/repos/{owner}/{repo}/contents/{path}", data=data)
        
        if success:
            logger.info(f"Created/updated file: {owner}/{repo}/{path}")
            return True, response
        else:
            logger.error(f"Failed to create/update file: {owner}/{repo}/{path}")
            return False, response
    
    def create_directory_structure(self, owner: str, repo: str, 
                                  structure: Dict[str, Any], base_path: str = "",
                                  message_prefix: str = "Add", branch: str = "main") -> List[Tuple[bool, str]]:
        """
        Create directory structure with files.
        
        Args:
            owner: Repository owner
            repo: Repository name
            structure: Nested dictionary with file paths and contents
            base_path: Base path for all files
            message_prefix: Prefix for commit messages
            branch: Target branch
            
        Returns:
            List of (success, file_path) tuples
        """
        results = []
        
        def process_node(node: Dict[str, Any], current_path: str):
            for key, value in node.items():
                file_path = f"{current_path}/{key}" if current_path else key
                
                if isinstance(value, dict):
                    # It's a directory, process recursively
                    process_node(value, file_path)
                else:
                    # It's a file
                    full_path = f"{base_path}/{file_path}" if base_path else file_path
                    message = f"{message_prefix} {file_path}"
                    
                    success, _ = self.create_file(
                        owner=owner,
                        repo=repo,
                        path=full_path,
                        content=value,
                        message=message,
                        branch=branch
                    )
                    
                    results.append((success, full_path))
        
        process_node(structure, "")
        return results
    
    def get_file_content(self, owner: str, repo: str, path: str, 
                        branch: str = "main") -> Tuple[bool, Optional[str]]:
        """
        Get file content from repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: File path
            branch: Branch name
            
        Returns:
            Tuple of (success, file_content)
        """
        success, response = self._make_request(
            "GET", 
            f"/repos/{owner}/{repo}/contents/{path}",
            params={"ref": branch}
        )
        
        if success and "content" in response:
            # Decode base64 content
            content = base64.b64decode(response["content"]).decode()
            return True, content
        else:
            return False, None
    
    def list_branches(self, owner: str, repo: str) -> Tuple[bool, Optional[List[str]]]:
        """
        List all branches in repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Tuple of (success, list_of_branches)
        """
        success, response = self._make_request("GET", f"/repos/{owner}/{repo}/branches")
        
        if success:
            branches = [branch["name"] for branch in response]
            return True, branches
        else:
            return False, None
    
    def create_branch(self, owner: str, repo: str, branch_name: str, 
                     from_branch: str = "main") -> Tuple[bool, Optional[Dict]]:
        """
        Create a new branch.
        
        Args:
            owner: Repository owner
            repo: Repository name
            branch_name: New branch name
            from_branch: Source branch
            
        Returns:
            Tuple of (success, response_data)
        """
        # Get SHA of the source branch
        success, ref_data = self._make_request(
            "GET", 
            f"/repos/{owner}/{repo}/git/refs/heads/{from_branch}"
        )
        
        if not success:
            return False, ref_data
        
        sha = ref_data["object"]["sha"]
        
        # Create new branch
        data = {
            "ref": f"refs/heads/{branch_name}",
            "sha": sha
        }
        
        success, response = self._make_request("POST", f"/repos/{owner}/{repo}/git/refs", data=data)
        
        if success:
            logger.info(f"Created branch: {branch_name} in {owner}/{repo}")
            return True, response
        else:
            logger.error(f"Failed to create branch: {branch_name} in {owner}/{repo}")
            return False, response
    
    def create_pull_request(self, owner: str, repo: str, title: str, 
                           head: str, base: str = "main", body: str = "") -> Tuple[bool, Optional[Dict]]:
        """
        Create a pull request.
        
        Args:
            owner: Repository owner
            repo: Repository name
            title: PR title
            head: Source branch
            base: Target branch
            body: PR description
            
        Returns:
            Tuple of (success, PR_data)
        """
        data = {
            "title": title,
            "head": head,
            "base": base,
            "body": body
        }
        
        success, response = self._make_request("POST", f"/repos/{owner}/{repo}/pulls", data=data)
        
        if success:
            logger.info(f"Created PR: {title} in {owner}/{repo}")
            return True, response
        else:
            logger.error(f"Failed to create PR: {title} in {owner}/{repo}")
            return False, response
    
    def create_webhook(self, owner: str, repo: str, webhook_url: str, 
                      events: List[str] = None, secret: str = None) -> Tuple[bool, Optional[Dict]]:
        """
        Create a webhook for the repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            webhook_url: URL to send webhook events to
            events: List of events to subscribe to
            secret: Webhook secret for verification
            
        Returns:
            Tuple of (success, webhook_data)
        """
        if events is None:
            events = ["push", "pull_request", "issues"]
        
        data = {
            "name": "web",
            "active": True,
            "events": events,
            "config": {
                "url": webhook_url,
                "content_type": "json",
                "insecure_ssl": "0"
            }
        }
        
        if secret:
            data["config"]["secret"] = secret
        
        success, response = self._make_request("POST", f"/repos/{owner}/{repo}/hooks", data=data)
        
        if success:
            logger.info(f"Created webhook for {owner}/{repo}")
            return True, response
        else:
            logger.error(f"Failed to create webhook for {owner}/{repo}")
            return False, response
    
    def list_webhooks(self, owner: str, repo: str) -> Tuple[bool, Optional[List[Dict]]]:
        """
        List all webhooks for repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Tuple of (success, list_of_webhooks)
        """
        return self._make_request("GET", f"/repos/{owner}/{repo}/hooks")
    
    def delete_webhook(self, owner: str, repo: str, hook_id: int) -> Tuple[bool, Optional[Dict]]:
        """
        Delete a webhook.
        
        Args:
            owner: Repository owner
            repo: Repository name
            hook_id: Webhook ID
            
        Returns:
            Tuple of (success, response_data)
        """
        success, response = self._make_request("DELETE", f"/repos/{owner}/{repo}/hooks/{hook_id}")
        
        if success:
            logger.info(f"Deleted webhook {hook_id} from {owner}/{repo}")
            return True, response
        else:
            logger.error(f"Failed to delete webhook {hook_id} from {owner}/{repo}")
            return False, response
    
    def create_issue(self, owner: str, repo: str, title: str, 
                    body: str = "", labels: List[str] = None) -> Tuple[bool, Optional[Dict]]:
        """
        Create an issue.
        
        Args:
            owner: Repository owner
            repo: Repository name
            title: Issue title
            body: Issue description
            labels: List of labels
            
        Returns:
            Tuple of (success, issue_data)
        """
        data = {
            "title": title,
            "body": body
        }
        
        if labels:
            data["labels"] = labels
        
        success, response = self._make_request("POST", f"/repos/{owner}/{repo}/issues", data=data)
        
        if success:
            logger.info(f"Created issue: {title} in {owner}/{repo}")
            return True, response
        else:
            logger.error(f"Failed to create issue: {title} in {owner}/{repo}")
            return False, response
    
    def search_repositories(self, query: str, sort: str = "stars", 
                           order: str = "desc", per_page: int = 10) -> Tuple[bool, Optional[List[Dict]]]:
        """
        Search for repositories.
        
        Args:
            query: Search query
            sort: Sort field (stars, forks, updated)
            order: Sort order (asc, desc)
            per_page: Results per page
            
        Returns:
            Tuple of (success, search_results)
        """
        params = {
            "q": query,
            "sort": sort,
            "order": order,
            "per_page": per_page
        }
        
        success, response = self._make_request("GET", "/search/repositories", params=params)
        
        if success:
            return True, response.get("items", [])
        else:
            return False, None
    
    def get_repository_languages(self, owner: str, repo: str) -> Tuple[bool, Optional[Dict]]:
        """
        Get repository language statistics.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Tuple of (success, language_data)
        """
        return self._make_request("GET", f"/repos/{owner}/{repo}/languages")
    
    def get_repository_readme(self, owner: str, repo: str, branch: str = "main") -> Tuple[bool, Optional[str]]:
        """
        Get repository README content.
        
        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch name
            
        Returns:
            Tuple of (success, README_content)
        """
        return self.get_file_content(owner, repo, "README.md", branch)
    
    def update_repository_settings(self, owner: str, repo: str, 
                                 settings: Dict[str, Any]) -> Tuple[bool, Optional[Dict]]:
        """
        Update repository settings.
        
        Args:
            owner: Repository owner
            repo: Repository name
            settings: Dictionary of settings to update
            
        Returns:
            Tuple of (success, response_data)
        """
        success, response = self._make_request("PATCH", f"/repos/{owner}/{repo}", data=settings)
        
        if success:
            logger.info(f"Updated settings for {owner}/{repo}")
            return True, response
        else:
            logger.error(f"Failed to update settings for {owner}/{repo}")
            return False, response
    
    def get_collaborators(self, owner: str, repo: str) -> Tuple[bool, Optional[List[Dict]]]:
        """
        Get repository collaborators.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Tuple of (success, list_of_collaborators)
        """
        return self._make_request("GET", f"/repos/{owner}/{repo}/collaborators")
    
    def add_collaborator(self, owner: str, repo: str, username: str, 
                        permission: str = "push") -> Tuple[bool, Optional[Dict]]:
        """
        Add collaborator to repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            username: GitHub username
            permission: Permission level (pull, push, admin)
            
        Returns:
            Tuple of (success, response_data)
        """
        data = {"permission": permission}
        success, response = self._make_request("PUT", f"/repos/{owner}/{repo}/collaborators/{username}", data=data)
        
        if success:
            logger.info(f"Added collaborator {username} to {owner}/{repo}")
            return True, response
        else:
            logger.error(f"Failed to add collaborator {username} to {owner}/{repo}")
            return False, response
    
    def remove_collaborator(self, owner: str, repo: str, username: str) -> Tuple[bool, Optional[Dict]]:
        """
        Remove collaborator from repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            username: GitHub username
            
        Returns:
            Tuple of (success, response_data)
        """
        success, response = self._make_request("DELETE", f"/repos/{owner}/{repo}/collaborators/{username}")
        
        if success:
            logger.info(f"Removed collaborator {username} from {owner}/{repo}")
            return True, response
        else:
            logger.error(f"Failed to remove collaborator {username} from {owner}/{repo}")
            return False, response
    
    def generate_project_structure(self, project_name: str, bot_type: str = "general") -> Dict[str, Any]:
        """
        Generate a standard project structure for a bot.
        
        Args:
            project_name: Name of the project
            bot_type: Type of bot (general, discord, telegram, etc.)
            
        Returns:
            Dictionary representing the project structure
        """
        structure = {
            "README.md": f"""# {project_name}

{project_name} - An AI-powered bot created with BotManager V2.5

## Features
- AI-powered responses
- Multi-platform support
- Easy configuration
- Extensible architecture

## Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure environment variables
4. Run the bot: `python main.py`

## Configuration

Copy `.env.example` to `.env` and fill in your API keys.

## License

MIT License
""",
            
            "requirements.txt": """requests>=2.28.0
python-dotenv>=0.21.0
openai>=0.27.0
aiohttp>=3.8.0
asyncio>=3.4.3
""",
            
            ".env.example": """# API Keys
OPENAI_API_KEY=your_openai_api_key_here
DISCORD_TOKEN=your_discord_token_here
TELEGRAM_TOKEN=your_telegram_token_here

# Configuration
BOT_NAME=MyBot
DEBUG_MODE=True
LOG_LEVEL=INFO
""",
            
            "main.py": """#!/usr/bin/env python3
"""
        }
        
        # Add bot-specific files based on type
        if bot_type == "discord":
            structure["bot"] = {
                "__init__.py": "",
                "discord_bot.py": """import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
    async def setup_hook(self):
        # Load cogs here
        pass
        
    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')

def main():
    bot = DiscordBot()
    bot.run(os.getenv('DISCORD_TOKEN'))

if __name__ == '__main__':
    main()
"""
            }
        
        elif bot_type == "telegram":
            structure["bot"] = {
                "__init__.py": "",
                "telegram_bot.py": """import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context):
    await update.message.reply_text('Hello! I am your Telegram bot.')

async def echo(update: Update, context):
    await update.message.reply_text(update.message.text)

def main():
    application = Application.builder().token(os.getenv('TELEGRAM_TOKEN')).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    application.run_polling()

if __name__ == '__main__':
    main()
"""
            }
        
        # Add common directories
        structure["utils"] = {
            "__init__.py": "",
            "config.py": """import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_NAME = os.getenv('BOT_NAME', 'MyBot')
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    @classmethod
    def validate(cls):
        required_vars = ['OPENAI_API_KEY']
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {missing}")
"""
        }
        
        structure["tests"] = {
            "__init__.py": "",
            "test_basic.py": """import unittest
from utils.config import Config

class TestConfig(unittest.TestCase):
    def test_config_validation(self):
        # Test configuration validation
        self.assertTrue(hasattr(Config, 'BOT_NAME'))

if __name__ == '__main__':
    unittest.main()
"""
        }
        
        return structure
    
    def create_bot_project(self, project_name: str, description: str = "", 
                          bot_type: str = "general", private: bool = False) -> Tuple[bool, Optional[Dict]]:
        """
        Create a complete bot project repository.
        
        Args:
            project_name: Name of the project/repository
            description: Project description
            bot_type: Type of bot
            private: Whether repository is private
            
        Returns:
            Tuple of (success, project_data)
        """
        # Create repository
        success, repo_data = self.create_repository(
            name=project_name,
            description=description or f"{project_name} - AI Bot Project",
            private=private,
            auto_init=True
        )
        
        if not success:
            return False, repo_data
        
        owner = repo_data["owner"]["login"]
        repo_name = repo_data["name"]
        
        # Generate project structure
        structure = self.generate_project_structure(project_name, bot_type)
        
        # Create files
        results = self.create_directory_structure(
            owner=owner,
            repo=repo_name,
            structure=structure,
            message_prefix="Initialize"
        )
        
        # Check results
        failed_files = [path for success, path in results if not success]
        
        if failed_files:
            logger.warning(f"Some files failed to create: {failed_files}")
        
        # Create additional files
        additional_files = {
            ".gitignore": """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.env
.venv
.env.local
.env.development.local
.env.test.local
.env.production.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
""",
            
            "LICENSE": """MIT License

Copyright (c) 2024 BotManager V2.5

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
        }
        
        for filename, content in additional_files.items():
            self.create_file(
                owner=owner,
                repo=repo_name,
                path=filename,
                content=content,
                message=f"Add {filename}"
            )
        
        # Add project metadata
        metadata = {
            "project": project_name,
            "type": bot_type,
            "created": datetime.now().isoformat(),
            "botmanager_version": "2.5",
            "repository": repo_data["html_url"]
        }
        
        self.create_file(
            owner=owner,
            repo=repo_name,
            path=".botmanager.json",
            content=json.dumps(metadata, indent=2),
            message="Add BotManager metadata"
        )
        
        return True, {
            "repository": repo_data,
            "files_created": len([r for r in results if r[0]]),
            "files_failed": len(failed_files),
            "html_url": repo_data["html_url"],
            "clone_url": repo_data["clone_url"],
            "metadata": metadata
        }


# Utility functions for common operations
def create_github_handler() -> GitHubHandler:
    """Create and return a GitHubHandler instance."""
    return GitHubHandler()


def verify_github_token(token: str) -> bool:
    """
    Verify if a GitHub token is valid.
    
    Args:
        token: GitHub token to verify
        
    Returns:
        True if token is valid, False otherwise
    """
    try:
        handler = GitHubHandler(token)
        user_info = handler.get_user_info()
        return user_info is not None
    except Exception:
        return False


def get_repository_url(owner: str, repo: str) -> str:
    """
    Get repository URL.
    
    Args:
        owner: Repository owner
        repo: Repository name
        
    Returns:
        Repository URL
    """
    return f"https://github.com/{owner}/{repo}"


if __name__ == "__main__":
    # Example usage
    handler = GitHubHandler()
    
    # Test connection
    user_info = handler.get_user_info()
    if user_info:
        print(f"Connected as: {user_info.get('login')}")
        
        # Create a test repository
        success, repo = handler.create_repository(
            name="test-bot-project",
            description="Test bot project",
            private=True
        )
        
        if success:
            print(f"Created repository: {repo['html_url']}")
    else:
        print("Failed to connect to GitHub")