"""
BotManager V2.5 - Enhanced AI Project Generator with Multi-Bot Support
Main application file with Flask backend and React frontend integration
"""

import os
import json
import logging
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import openai
from anthropic import Anthropic
import google.generativeai as genai
from groq import Groq
import replicate
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, 
            static_folder='../frontend/build',
            template_folder='../frontend/build')
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Configuration from environment variables
class Config:
    """Application configuration from environment variables"""
    # OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_ORG_ID = os.getenv('OPENAI_ORG_ID')
    
    # Anthropic
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    
    # Google Gemini
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    
    # Groq
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    
    # Replicate
    REPLICATE_API_TOKEN = os.getenv('REPLICATE_API_TOKEN')
    
    # Hugging Face
    HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY')
    
    # Cohere
    COHERE_API_KEY = os.getenv('COHERE_API_KEY')
    
    # Stability AI
    STABILITY_API_KEY = os.getenv('STABILITY_API_KEY')
    
    # ElevenLabs
    ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
    
    # AssemblyAI
    ASSEMBLYAI_API_KEY = os.getenv('ASSEMBLYAI_API_KEY')
    
    # App settings
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    MAX_PROJECTS = int(os.getenv('MAX_PROJECTS', '100'))
    MAX_BOTS_PER_PROJECT = int(os.getenv('MAX_BOTS_PER_PROJECT', '10'))

# Initialize AI clients
def initialize_ai_clients():
    """Initialize all AI API clients"""
    clients = {}
    
    try:
        # OpenAI
        if Config.OPENAI_API_KEY:
            openai.api_key = Config.OPENAI_API_KEY
            if Config.OPENAI_ORG_ID:
                openai.organization = Config.OPENAI_ORG_ID
            clients['openai'] = openai
            logger.info("OpenAI client initialized")
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI: {e}")
    
    try:
        # Anthropic
        if Config.ANTHROPIC_API_KEY:
            clients['anthropic'] = Anthropic(api_key=Config.ANTHROPIC_API_KEY)
            logger.info("Anthropic client initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Anthropic: {e}")
    
    try:
        # Google Gemini
        if Config.GOOGLE_API_KEY:
            genai.configure(api_key=Config.GOOGLE_API_KEY)
            clients['gemini'] = genai
            logger.info("Google Gemini client initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Google Gemini: {e}")
    
    try:
        # Groq
        if Config.GROQ_API_KEY:
            clients['groq'] = Groq(api_key=Config.GROQ_API_KEY)
            logger.info("Groq client initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Groq: {e}")
    
    try:
        # Replicate
        if Config.REPLICATE_API_TOKEN:
            clients['replicate'] = replicate.Client(api_token=Config.REPLICATE_API_TOKEN)
            logger.info("Replicate client initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Replicate: {e}")
    
    return clients

# Initialize clients
ai_clients = initialize_ai_clients()

# Data models
class BotType(Enum):
    """Types of AI bots supported"""
    CHAT = "chat"
    CODE = "code"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    ANALYTICS = "analytics"
    AUTOMATION = "automation"
    RESEARCH = "research"
    CUSTOM = "custom"

class BotStatus(Enum):
    """Bot status states"""
    CREATED = "created"
    TRAINING = "training"
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    DELETED = "deleted"

class ProjectStatus(Enum):
    """Project status states"""
    DRAFT = "draft"
    PLANNING = "planning"
    DEVELOPMENT = "development"
    TESTING = "testing"
    DEPLOYED = "deployed"
    MAINTENANCE = "maintenance"
    ARCHIVED = "archived"

@dataclass
class BotConfig:
    """Configuration for a single bot"""
    bot_id: str
    name: str
    bot_type: BotType
    description: str
    provider: str
    model: str
    parameters: Dict[str, Any]
    capabilities: List[str]
    status: BotStatus
    created_at: str
    updated_at: str
    training_data: Optional[List[Dict]] = None
    performance_metrics: Optional[Dict[str, float]] = None
    
    def to_dict(self):
        return asdict(self)

@dataclass
class Project:
    """Project containing multiple bots"""
    project_id: str
    name: str
    description: str
    status: ProjectStatus
    created_at: str
    updated_at: str
    owner: str
    bots: List[BotConfig]
    tags: List[str]
    settings: Dict[str, Any]
    
    def to_dict(self):
        return asdict(self)

# In-memory storage (replace with database in production)
projects_db: Dict[str, Project] = {}
bots_db: Dict[str, BotConfig] = {}

# AI Service Manager
class AIServiceManager:
    """Manages interactions with different AI providers"""
    
    @staticmethod
    def generate_with_openai(prompt: str, model: str = "gpt-4", **kwargs) -> Dict:
        """Generate content using OpenAI"""
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            return {
                "success": True,
                "content": response.choices[0].message.content,
                "model": model,
                "usage": response.usage.to_dict() if hasattr(response, 'usage') else None
            }
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def generate_with_anthropic(prompt: str, model: str = "claude-3-opus-20240229", **kwargs) -> Dict:
        """Generate content using Anthropic Claude"""
        try:
            client = ai_clients.get('anthropic')
            if not client:
                return {"success": False, "error": "Anthropic client not initialized"}
            
            response = client.messages.create(
                model=model,
                max_tokens=kwargs.get('max_tokens', 1000),
                messages=[{"role": "user", "content": prompt}],
                **{k: v for k, v in kwargs.items() if k != 'max_tokens'}
            )
            return {
                "success": True,
                "content": response.content[0].text,
                "model": model,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                }
            }
        except Exception as e:
            logger.error(f"Anthropic error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def generate_with_gemini(prompt: str, model: str = "gemini-pro", **kwargs) -> Dict:
        """Generate content using Google Gemini"""
        try:
            model_instance = genai.GenerativeModel(model)
            response = model_instance.generate_content(prompt, **kwargs)
            return {
                "success": True,
                "content": response.text,
                "model": model,
                "usage": None  # Gemini doesn't provide usage in response
            }
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def generate_with_groq(prompt: str, model: str = "mixtral-8x7b-32768", **kwargs) -> Dict:
        """Generate content using Groq"""
        try:
            client = ai_clients.get('groq')
            if not client:
                return {"success": False, "error": "Groq client not initialized"}
            
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            return {
                "success": True,
                "content": response.choices[0].message.content,
                "model": model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
        except Exception as e:
            logger.error(f"Groq error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def generate_image(prompt: str, provider: str = "openai", **kwargs) -> Dict:
        """Generate images using various providers"""
        try:
            if provider == "openai":
                response = openai.Image.create(
                    prompt=prompt,
                    n=kwargs.get('n', 1),
                    size=kwargs.get('size', '1024x1024'),
                    **{k: v for k, v in kwargs.items() if k not in ['n', 'size']}
                )
                return {
                    "success": True,
                    "images": [img.url for img in response.data],
                    "provider": provider
                }
            elif provider == "replicate":
                client = ai_clients.get('replicate')
                if not client:
                    return {"success": False, "error": "Replicate client not initialized"}
                
                model = kwargs.get('model', "stability-ai/stable-diffusion")
                output = client.run(
                    model,
                    input={"prompt": prompt, **kwargs}
                )
                return {
                    "success": True,
                    "images": output if isinstance(output, list) else [output],
                    "provider": provider
                }
            else:
                return {"success": False, "error": f"Unsupported provider: {provider}"}
        except Exception as e:
            logger.error(f"Image generation error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def generate_code(prompt: str, language: str = "python", **kwargs) -> Dict:
        """Generate code using AI"""
        enhanced_prompt = f"""Generate {language} code based on the following requirements:
        
        Requirements: {prompt}
        
        Provide only the code with appropriate comments and documentation.
        Ensure the code follows best practices and includes error handling."""
        
        # Use the most capable model available
        providers = ['openai', 'anthropic', 'gemini', 'groq']
        for provider in providers:
            if provider in ai_clients:
                if provider == 'openai':
                    return AIServiceManager.generate_with_openai(enhanced_prompt, model="gpt-4", **kwargs)
                elif provider == 'anthropic':
                    return AIServiceManager.generate_with_anthropic(enhanced_prompt, **kwargs)
                elif provider == 'gemini':
                    return AIServiceManager.generate_with_gemini(enhanced_prompt, **kwargs)
                elif provider == 'groq':
                    return AIServiceManager.generate_with_groq(enhanced_prompt, **kwargs)
        
        return {"success": False, "error": "No AI providers available"}

# Project Generator
class ProjectGenerator:
    """Generates complete AI projects with multiple bots"""
    
    @staticmethod
    def generate_project_plan(requirements: str) -> Dict:
        """Generate a project plan based on requirements"""
        prompt = f"""Based on the following requirements, create a comprehensive AI project plan:

Requirements: {requirements}

Provide a JSON response with:
1. project_name: A creative name for the project
2. description: Detailed project description
3. objectives: List of project objectives
4. bots: List of bots needed, each with:
   - name: Bot name
   - type: Type of bot (chat, code, image, etc.)
   - description: What the bot does
   - capabilities: List of capabilities
   - suggested_provider: Recommended AI provider
5. architecture: High-level architecture description
6. timeline: Estimated timeline with phases
7. resources: Required resources and dependencies
8. risks: Potential risks and mitigation strategies

Return ONLY valid JSON."""
        
        # Try multiple providers for best results
        providers = ['openai', 'anthropic', 'gemini']
        for provider in providers:
            if provider in ai_clients:
                if provider == 'openai':
                    result = AIServiceManager.generate_with_openai(prompt, model="gpt-4", temperature=0.7)
                elif provider == 'anthropic':
                    result = AIServiceManager.generate_with_anthropic(prompt, temperature=0.7)
                elif provider == 'gemini':
                    result = AIServiceManager.generate_with_gemini(prompt, temperature=0.7)
                
                if result['success']:
                    try:
                        # Extract JSON from response
                        content = result['content']
                        # Find JSON in the response
                        start = content.find('{')
                        end = content.rfind('}') + 1
                        if start != -1 and end != 0:
                            json_str = content[start:end]
                            plan = json.loads(json_str)
                            return {"success": True, "plan": plan}
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON parsing error: {e}")
                        continue
        
        return {"success": False, "error": "Failed to generate project plan"}
    
    @staticmethod
    def create_bot_config(bot_spec: Dict) -> BotConfig:
        """Create bot configuration from specification"""
        bot_id = f"bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(str(bot_spec)) % 10000:04d}"
        
        return BotConfig(
            bot_id=bot_id,
            name=bot_spec.get('name', 'Unnamed Bot'),
            bot_type=BotType(bot_spec.get('type', 'chat')),
            description=bot_spec.get('description', ''),
            provider=bot_spec.get('suggested_provider', 'openai'),
            model=bot_spec.get('model', 'gpt-3.5-turbo'),
            parameters=bot_spec.get('parameters', {}),
            capabilities=bot_spec.get('capabilities', []),
            status=BotStatus.CREATED,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            training_data=[],
            performance_metrics={}
        )
    
    @staticmethod
    def generate_project_code(project_plan: Dict) -> Dict:
        """Generate code for the entire project"""
        prompt = f"""Generate a complete Python Flask application for the following AI project:

Project Name: {project_plan.get('project_name')}
Description: {project_plan.get('description')}
Bots: {json.dumps(project_plan.get('bots', []), indent=2)}

Include:
1. Main app.py with Flask server
2. Bot manager class
3. Individual bot implementations
4. API endpoints
5. Configuration management
6. Error handling
7. Logging
8. Requirements.txt

Structure the code properly with comments and documentation."""

        result = AIServiceManager.generate_code(prompt, language="python")
        if result['success']:
            # Parse and structure the generated code
            code_content = result['content']
            # Extract code blocks if present
            if '```python' in code_content:
                code_content = code_content.split('```python')[1].split('```')[0]
            elif '```' in code_content:
                code_content = code_content.split('```')[1].split('```')[0]
            
            return {
                "success": True,
                "code": code_content.strip(),
                "files": {
                    "app.py": code_content,
                    "requirements.txt": ProjectGenerator.generate_requirements(project_plan),
                    "README.md": ProjectGenerator.generate_readme(project_plan)
                }
            }
        
        return result
    
    @staticmethod
    def generate_requirements(project_plan: Dict) -> str:
        """Generate requirements.txt based on project needs"""
        base_requirements = """flask>=2.3.0
flask-cors>=4.0.0
flask-socketio>=5.3.0
python-dotenv>=1.0.0
openai>=1.0.0
anthropic>=0.8.0
google-generativeai>=0.3.0
groq>=0.3.0
replicate>=0.19.0
requests>=2.31.0
"""
        
        # Add provider-specific requirements
        bots = project_plan.get('bots', [])
        providers = set(bot.get('suggested_provider', 'openai') for bot in bots)
        
        additional = ""
        if 'anthropic' in providers:
            additional += "anthropic>=0.8.0\n"
        if 'google' in providers or 'gemini' in providers:
            additional += "google-generativeai>=0.3.0\n"
        if 'groq' in providers:
            additional += "groq>=0.3.0\n"
        if 'replicate' in providers:
            additional += "replicate>=0.19.0\n"
        
        return base_requirements + additional
    
    @staticmethod
    def generate_readme(project_plan: Dict) -> str:
        """Generate README.md for the project"""
        readme = f"""# {project_plan.get('project_name', 'AI Project')}

{project_plan.get('description', '')}

## Project Overview

This project implements an AI-powered application with multiple specialized bots.

## Bots

"""
        
        for bot in project_plan.get('bots', []):
            readme += f"""### {bot.get('name')}
- **Type**: {bot.get('type')}
- **Description**: {bot.get('description')}
- **Capabilities**: {', '.join(bot.get('capabilities', []))}
- **Provider**: {bot.get('suggested_provider', 'openai')}

"""
        
        readme += """## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables (see .env.example)
4. Run the application: `python app.py`

## Configuration

Copy `.env.example` to `.env` and fill in your API keys:

```
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GOOGLE_API_KEY=your_google_key
# Add other API keys as needed
```

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/projects` - List all projects
- `POST /api/projects` - Create new project
- `GET /api/projects/{id}` - Get project details
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project
- `POST /api/projects/{id}/generate` - Generate project code
- `GET /api/bots` - List all bots
- `POST /api/bots` - Create new bot
- `POST /api/bots/{id}/chat` - Chat with bot
- `POST /api/bots/{id}/generate` - Generate content with bot

## WebSocket Events

- `connect` - Client connection
- `disconnect` - Client disconnection
- `bot_update` - Bot status updates
- `project_update` - Project status updates
- `generation_progress` - Code generation progress

## Development

The project uses Flask for the backend and can be extended with a React frontend.

## License

MIT
"""
        
        return readme

# API Routes
@app.route('/')
def serve_frontend():
    """Serve the React frontend"""
    return render_template('index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory(app.static_folder, path)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.5.0",
        "providers_available": list(ai_clients.keys())
    })

# Project Management Endpoints
@app.route('/api/projects', methods=['GET'])
def get_projects():
    """Get all projects"""
    projects = [project.to_dict() for project in projects_db.values()]
    return jsonify({
        "success": True,
        "projects": projects,
        "count": len(projects)
    })

@app.route('/api/projects', methods=['POST'])
def create_project():
    """Create a new project"""
    try:
        data = request.get_json()
        
        # Validate input
        if not data or 'name' not in data:
            return jsonify({
                "success": False,
                "error": "Project name is required"
            }), 400
        
        # Check project limit
        if len(projects_db) >= Config.MAX_PROJECTS:
            return jsonify({
                "success": False,
                "error": f"Maximum number of projects ({Config.MAX_PROJECTS}) reached"
            }), 400
        
        project_id = f"proj_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(data['name']) % 10000:04d}"
        
        project = Project(
            project_id=project_id,
            name=data['name'],
            description=data.get('description', ''),
            status=ProjectStatus.DRAFT,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            owner=data.get('owner', 'anonymous'),
            bots=[],
            tags=data.get('tags', []),
            settings=data.get('settings', {})
        )
        
        projects_db[project_id] = project
        
        # Emit WebSocket event
        socketio.emit('project_update', {
            'type': 'created',
            'project_id': project_id,
            'project': project.to_dict()
        })
        
        return jsonify({
            "success": True,
            "project_id": project_id,
            "project": project.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    """Get a specific project"""
    if project_id not in projects_db:
        return jsonify({
            "success": False,
            "error": "Project not found"
        }), 404
    
    return jsonify({
        "success": True,
        "project": projects_db[project_id].to_dict()
    })

@app.route('/api/projects/<project_id>', methods=['PUT'])
def update_project(project_id):
    """Update a project"""
    if project_id not in projects_db:
        return jsonify({
            "success": False,
            "error": "Project not found"
        }), 404
    
    try:
        data = request.get_json()
        project = projects_db[project_id]
        
        # Update fields
        if 'name' in data:
            project.name = data['name']
        if 'description' in data:
            project.description = data['description']
        if 'status' in data:
            project.status = ProjectStatus(data['status'])
        if 'tags' in data:
            project.tags = data['tags']
        if 'settings' in data:
            project.settings.update(data['settings'])
        
        project.updated_at = datetime.now().isoformat()
        
        # Emit WebSocket event
        socketio.emit('project_update', {
            'type': 'updated',
            'project_id': project_id,
            'project': project.to_dict()
        })
        
        return jsonify({
            "success": True,
            "project": project.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error updating project: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/projects/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Delete a project"""
    if project_id not in projects_db:
        return jsonify({
            "success": False,
            "error": "Project not found"
        }), 404
    
    try:
        # Remove all bots in the project
        project = projects_db[project_id]
        for bot in project.bots:
            if bot.bot_id in bots_db:
                del bots_db[bot.bot_id]
        
        # Remove project
        del projects_db[project_id]
        
        # Emit WebSocket event
        socketio.emit('project_update', {
            'type': 'deleted',
            'project_id': project_id
        })
        
        return jsonify({
            "success": True,
            "message": "Project deleted successfully"
        })
        
    except Exception as e:
        logger.error(f"Error deleting project: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/projects/<project_id>/generate-plan', methods=['POST'])
def generate_project_plan(project_id):
    """Generate a project plan based on requirements"""
    if project_id not in projects_db:
        return jsonify({
            "success": False,
            "error": "Project not found"
        }), 404
    
    try:
        data = request.get_json()
        requirements = data.get('requirements', '')
        
        if not requirements:
            return jsonify({
                "success": False,
                "error": "Requirements are required"
            }), 400
        
        # Generate project plan
        result = ProjectGenerator.generate_project_plan(requirements)
        
        if not result['success']:
            return jsonify(result), 500
        
        # Update project with generated plan
        project = projects_db[project_id]
        project_plan = result['plan']
        
        # Create bots from plan
        bots = []
        for bot_spec in project_plan.get('bots', []):
            bot_config = ProjectGenerator.create_bot_config(bot_spec)
            bots.append(bot_config)
            bots_db[bot_config.bot_id] = bot_config
        
        project.bots = bots
        project.description = project_plan.get('description', project.description)
        project.status = ProjectStatus.PLANNING
        project.updated_at = datetime.now().isoformat()
        project.settings['generated_plan'] = project_plan
        
        # Emit WebSocket event
        socketio.emit('project_update', {
            'type': 'plan_generated',
            'project_id': project_id,
            'plan': project_plan
        })
        
        return jsonify({
            "success": True,
            "plan": project_plan,
            "project": project.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error generating project plan: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/projects/<project_id>/generate-code', methods=['POST'])
def generate_project_code(project_id):
    """Generate code for a project"""
    if project_id not in projects_db:
        return jsonify({
            "success": False,
            "error": "Project not found"
        }), 404
    
    try:
        project = projects_db[project_id]
        
        if 'generated_plan' not in project.settings:
            return jsonify({
                "success": False,
                "error": "Project plan not found. Generate a plan first."
            }), 400
        
        # Generate code
        result = ProjectGenerator.generate_project_code(project.settings['generated_plan'])
        
        if not result['success']:
            return jsonify(result), 500
        
        # Update project
        project.status = ProjectStatus.DEVELOPMENT
        project.updated_at = datetime.now().isoformat()
        project.settings['generated_code'] = result
        
        # Emit WebSocket events for progress
        socketio.emit('generation_progress', {
            'project_id': project_id,
            'stage': 'code_generation',
            'progress': 100,
            'message': 'Code generation complete'
        })
        
        return jsonify({
            "success": True,
            "code": result,
            "project": project.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error generating project code: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# Bot Management Endpoints
@app.route('/api/bots', methods=['GET'])
def get_bots():
    """Get all bots"""
    bots = [bot.to_dict() for bot in bots_db.values()]
    return jsonify({
        "success": True,
        "bots": bots,
        "count": len(bots)
    })

@app.route('/api/bots', methods=['POST'])
def create_bot():
    """Create a new bot"""
    try:
        data = request.get_json()
        
        # Validate input
        if not data or 'name' not in data:
            return jsonify({
                "success": False,
                "error": "Bot name is required"
            }), 400
        
        bot_id = f"bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(data['name']) % 10000:04d}"
        
        bot = BotConfig(
            bot_id=bot_id,
            name=data['name'],
            bot_type=BotType(data.get('type', 'chat')),
            description=data.get('description', ''),
            provider=data.get('provider', 'openai'),
            model=data.get('model', 'gpt-3.5-turbo'),
            parameters=data.get('parameters', {}),
            capabilities=data.get('capabilities', []),
            status=BotStatus.CREATED,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            training_data=data.get('training_data', []),
            performance_metrics={}
        )
        
        bots_db[bot_id] = bot
        
        # Emit WebSocket event
        socketio.emit('bot_update', {
            'type': 'created',
            'bot_id': bot_id,
            'bot': bot.to_dict()
        })
        
        return jsonify({
            "success": True,
            "bot_id": bot_id,
            "bot": bot.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating bot: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/bots/<bot_id>', methods=['GET'])
def get_bot(bot_id):
    """Get a specific bot"""
    if bot_id not in bots_db:
        return jsonify({
            "success": False,
            "error": "Bot not found"
        }), 404
    
    return jsonify({
        "success": True,
        "bot": bots_db[bot_id].to_dict()
    })

@app.route('/api/bots/<bot_id>/chat', methods=['POST'])
def chat_with_bot(bot_id):
    """Chat with a bot"""
    if bot_id not in bots_db:
        return jsonify({
            "success": False,
            "error": "Bot not found"
        }), 404
    
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        if not message:
            return jsonify({
                "success": False,
                "error": "Message is required"
            }), 400
        
        bot = bots_db[bot_id]
        
        # Prepare prompt based on bot type
        if bot.bot_type == BotType.CODE:
            prompt = f"As a code generation bot, respond to: {message}"
            result = AIServiceManager.generate_code(prompt, **bot.parameters)
        elif bot.bot_type == BotType.IMAGE:
            result = AIServiceManager.generate_image(message, provider=bot.provider, **bot.parameters)
        else:
            # Default to chat
            prompt = f"As {bot.name} ({bot.description}), respond to: {message}"
            
            # Use appropriate provider
            if bot.provider == 'openai':
                result = AIServiceManager.generate_with_openai(prompt, model=bot.model, **bot.parameters)
            elif bot.provider == 'anthropic':
                result = AIServiceManager.generate_with_anthropic(prompt, model=bot.model, **bot.parameters)
            elif bot.provider == 'gemini':
                result = AIServiceManager.generate_with_gemini(prompt, model=bot.model, **bot.parameters)
            elif bot.provider == 'groq':
                result = AIServiceManager.generate_with_groq(prompt, model=bot.model, **bot.parameters)
            else:
                result = {"success": False, "error": f"Unsupported provider: {bot.provider}"}
        
        # Update bot metrics
        if result['success']:
            bot.performance_metrics['total_requests'] = bot.performance_metrics.get('total_requests', 0) + 1
            bot.performance_metrics['last_used'] = datetime.now().isoformat()
            bot.updated_at = datetime.now().isoformat()
        
        # Emit WebSocket event
        socketio.emit('bot_update', {
            'type': 'chat_response',
            'bot_id': bot_id,
            'message': message,
            'response': result
        })
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error chatting with bot: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/bots/<bot_id>/train', methods=['POST'])
def train_bot(bot_id):
    """Train a bot with custom data"""
    if bot_id not in bots_db:
        return jsonify({
            "success": False,
            "error": "Bot not found"
        }), 404
    
    try:
        data = request.get_json()
        training_data = data.get('training_data', [])
        
        if not training_data:
            return jsonify({
                "success": False,
                "error": "Training data is required"
            }), 400
        
        bot = bots_db[bot_id]
        bot.status = BotStatus.TRAINING
        bot.updated_at = datetime.now().isoformat()
        
        # Emit training start
        socketio.emit('bot_update', {
            'type': 'training_started',
            'bot_id': bot_id,
            'data_size': len(training_data)
        })
        
        # Simulate training (in production, this would involve actual model training)
        # For now, just store the training data
        bot.training_data = training_data
        
        # Simulate training progress
        for i in range(1, 101, 10):
            socketio.emit('bot_update', {
                'type': 'training_progress',
                'bot_id': bot_id,
                'progress': i,
                'message': f'Training epoch {i//10}'
            })
            socketio.sleep(0.1)