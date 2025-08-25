import os
import uuid
import logging
import asyncio
from dotenv import load_dotenv
from .azure_credentials import get_azure_ai_projects_client

logger = logging.getLogger(__name__)
load_dotenv()

PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")
AGENT_NAME = os.getenv("DIAGRAM_AGENT_NAME", "architectai-diagram-agent")

_cached_agent_id = None
_cached_client = None


def get_diagram_agents_client():
    """
    Get Azure AI Projects client for diagram generation - automatically chooses SDK or REST API
    """
    global _cached_client
    
    if _cached_client:
        return _cached_client.agents
    
    if not PROJECT_ENDPOINT:
        raise ValueError("PROJECT_ENDPOINT environment variable is not configured.")
    
    if not PROJECT_ENDPOINT.startswith("https://"):
        raise ValueError(f"Invalid PROJECT_ENDPOINT format: {PROJECT_ENDPOINT}. Should start with https://")
    
    try:
        # This will automatically choose between SDK (managed identity) or REST API (API key)
        _cached_client = get_azure_ai_projects_client()
        logger.info(f"Created Diagram AI Projects client for endpoint: {PROJECT_ENDPOINT}")
        return _cached_client.agents
    except Exception as e:
        logger.error(f"Failed to create Azure AI Projects client for diagrams: {e}")
        raise Exception(f"Failed to create Azure AI Projects client for diagrams. Error: {str(e)}")


async def get_or_create_diagram_agent():
    """
    Get or create the diagram generation agent
    """
    global _cached_agent_id

    if _cached_agent_id:
        return _cached_agent_id

    try:
        agents_client = get_diagram_agents_client()
        
        # Check for existing agent
        existing_agents_task = agents_client.list_agents()
        if asyncio.iscoroutine(existing_agents_task):
            existing_agents = await existing_agents_task
        else:
            existing_agents = existing_agents_task
            
        for agent in existing_agents:
            # Handle both object and dictionary formats
            agent_name = agent.get("name") if isinstance(agent, dict) else getattr(agent, "name", None)
            agent_id = agent.get("id") if isinstance(agent, dict) else getattr(agent, "id", None)
            
            if agent_name == AGENT_NAME and agent_id:
                _cached_agent_id = agent_id
                logger.info(f"Found existing diagram agent: {agent_id}")
                return agent_id
    except Exception as e:
        logger.warning(f"Error listing diagram agents: {e}")

    # Create new agent if not found
    try:
        logger.info(f"Creating new diagram agent: {AGENT_NAME}")
        agents_client = get_diagram_agents_client()
        
        instructions = (
            "You are a Python diagram generator. Given a cloud architecture description, "
            "generate ONLY a valid Python code block using the `diagrams` package. "
            "Use the EXACT class names from this comprehensive Azure diagrams reference:\n\n"
            
            "ANALYTICS:\n"
            "- from diagrams.azure.analytics import AnalysisServices, DataExplorerClusters, DataFactories\n"
            "- from diagrams.azure.analytics import DataLakeAnalytics, DataLakeStoreGen1, Databricks\n"
            "- from diagrams.azure.analytics import EventHubClusters, EventHubs, Hdinsightclusters\n"
            "- from diagrams.azure.analytics import LogAnalyticsWorkspaces, StreamAnalyticsJobs, SynapseAnalytics\n\n"
            
            "COMPUTE:\n"
            "- from diagrams.azure.compute import AppServices, AutomanagedVM, AvailabilitySets\n"
            "- from diagrams.azure.compute import BatchAccounts, CitrixVirtualDesktopsEssentials, CloudServicesClassic\n"
            "- from diagrams.azure.compute import CloudServices, ContainerInstances, ContainerRegistries\n"
            "- from diagrams.azure.compute import DiskEncryptionSets, DiskSnapshots, Disks\n"
            "- from diagrams.azure.compute import FunctionApps, ImageDefinitions, ImageVersions\n"
            "- from diagrams.azure.compute import KubernetesServices, MeshApplications, OsImages\n"
            "- from diagrams.azure.compute import SAPHANAOnAzure, ServiceFabricClusters, SharedImageGalleries\n"
            "- from diagrams.azure.compute import SpringCloud, VMClassic, VMImages, VMLinux\n"
            "- from diagrams.azure.compute import VMScaleSet, VMWindows, VirtualMachines, Workspaces\n\n"
            
            "DATABASE:\n"
            "- from diagrams.azure.database import BlobStorage, CacheForRedis, CosmosDb\n"
            "- from diagrams.azure.database import DataExplorerClusters, DataFactory, DatabaseForMariaDBServers\n"
            "- from diagrams.azure.database import DatabaseForMySQLServers, DatabaseForPostgreSQLServers, DatabaseMigrationServices\n"
            "- from diagrams.azure.database import ElasticDatabasePools, ElasticJobAgents, InstancePools\n"
            "- from diagrams.azure.database import ManagedDatabases, SQL, SQLDatabases, SQLDatawarehouse\n"
            "- from diagrams.azure.database import SQLManagedInstances, SQLServers, SQLServerStretchDatabases\n"
            "- from diagrams.azure.database import SQLVirtualMachines, SsisLiftAndShiftIr, VirtualClusters\n\n"
            
            "DEVOPS:\n"
            "- from diagrams.azure.devops import ApplicationInsights, Artifacts, Boards\n"
            "- from diagrams.azure.devops import DevopsStarter, DevtestLabs, LabServices\n"
            "- from diagrams.azure.devops import Pipelines, Repos, TestPlans\n\n"
            
            "GENERAL:\n"
            "- from diagrams.azure.general import Allresources, Azurehome, Developertools\n"
            "- from diagrams.azure.general import Helpsupport, Information, Managementgroups\n"
            "- from diagrams.azure.general import Marketplace, Quickstartcenter, Recent\n"
            "- from diagrams.azure.general import Reservations, Resource, Resourcegroups\n"
            "- from diagrams.azure.general import Servicehealth, Shareddashboard, Support\n"
            "- from diagrams.azure.general import Supportrequests, Tag, Tags, Twousericon\n"
            "- from diagrams.azure.general import Userprivacy, Userresource, Whatsnew\n\n"
            
            "INTEGRATION:\n"
            "- from diagrams.azure.integration import APIConnections, APIManagement, AppConfiguration\n"
            "- from diagrams.azure.integration import DataCatalog, EventGridDomains, EventGridSubscriptions\n"
            "- from diagrams.azure.integration import EventGridTopics, IntegrationAccounts, IntegrationServiceEnvironments\n"
            "- from diagrams.azure.integration import LogicAppsCustomConnector, LogicApps, PartnerTopic\n"
            "- from diagrams.azure.integration import SendgridAccounts, ServiceBusRelays, ServiceBus\n"
            "- from diagrams.azure.integration import SoftwareAsAService, StorsimpleDeviceManagers, SystemTopic\n\n"
            
            "IOT:\n"
            "- from diagrams.azure.iot import DeviceProvisioningServices, DigitalTwins, IotCentralApplications\n"
            "- from diagrams.azure.iot import IotHubSecurity, IotHub, Maps, Sphere\n"
            "- from diagrams.azure.iot import TimeSeriesInsightsEnvironments, TimeSeriesInsightsEventsSources, Windows10IotCoreServices\n\n"
            
            "ML (Machine Learning):\n"
            "- from diagrams.azure.ml import BatchAI, BotServices, CognitiveServices\n"
            "- from diagrams.azure.ml import GenomicsAccounts, MachineLearningServiceWorkspaces, MachineLearningStudioWebServicePlans\n"
            "- from diagrams.azure.ml import MachineLearningStudioWebServices, MachineLearningStudioWorkspaces\n\n"
            
            "MOBILE:\n"
            "- from diagrams.azure.mobile import AppServiceMobile, MobileEngagement, NotificationHubs\n\n"
            
            "NETWORK:\n"
            "- from diagrams.azure.network import ApplicationGateway, ApplicationSecurityGroups, CDNProfiles\n"
            "- from diagrams.azure.network import Connections, DDOSProtectionPlans, DNSPrivateZones\n"
            "- from diagrams.azure.network import DNSZones, ExpressRouteCircuits, Firewall\n"
            "- from diagrams.azure.network import FrontDoors, LoadBalancers, LocalNetworkGateways\n"
            "- from diagrams.azure.network import NetworkInterfaces, NetworkSecurityGroupsClassic, NetworkSecurityGroups\n"
            "- from diagrams.azure.network import NetworkWatcher, OnPremisesDataGateways, PublicIpAddresses\n"
            "- from diagrams.azure.network import ReservedIpAddressesClassic, RouteFilters, RouteTables\n"
            "- from diagrams.azure.network import ServiceEndpointPolicies, Subnets, TrafficManagerProfiles\n"
            "- from diagrams.azure.network import VirtualNetworkClassic, VirtualNetworkGateways, VirtualNetworks\n"
            "- from diagrams.azure.network import VirtualWans, VpnGateways\n\n"
            
            "SECURITY:\n"
            "- from diagrams.azure.security import ApplicationSecurityGroups, ConditionalAccess, Defender\n"
            "- from diagrams.azure.security import ExtendedSecurityUpdates, KeyVaults, SecurityCenter\n"
            "- from diagrams.azure.security import Sentinel\n\n"
            
            "STORAGE:\n"
            "- from diagrams.azure.storage import ArchiveStorage, Azurefxtedgefiler, BlobStorage\n"
            "- from diagrams.azure.storage import DataBoxEdgeDataBoxGateway, DataBox, DataLakeStorage\n"
            "- from diagrams.azure.storage import GeneralStorage, NetappFiles, QueuesStorage\n"
            "- from diagrams.azure.storage import StorageAccountsClassic, StorageAccounts, StorageExplorer\n"
            "- from diagrams.azure.storage import StorageSyncServices, TableStorage\n\n"
            
            "WEB:\n"
            "- from diagrams.azure.web import APIConnections, APIManagement, AppServiceCertificates\n"
            "- from diagrams.azure.web import AppServiceDomains, AppServiceEnvironments, AppServicePlans\n"
            "- from diagrams.azure.web import AppServices, MediaServices, NotificationHubNamespaces\n"
            "- from diagrams.azure.web import Search, Signalr\n\n"
            
            "CRITICAL RULES:\n"
            "1. Always use show=False in Diagram() constructor\n"
            "2. Use EXACT class names from the reference above - NO variations\n"
            "3. Import only what you need from each module\n"
            "4. Create meaningful node names and connections using >> operator\n"
            "5. Group related components logically\n"
            "6. Do NOT add explanations or markdown - ONLY Python code\n\n"
            
            "EXAMPLE PATTERN:\n"
            "```python\n"
            "from diagrams import Diagram\n"
            "from diagrams.azure.web import AppServices\n"
            "from diagrams.azure.database import SQLDatabases\n"
            "from diagrams.azure.security import KeyVaults\n\n"
            "with Diagram('Architecture', show=False):\n"
            "    webapp = AppServices('Web App')\n"
            "    db = SQLDatabases('Database')\n"
            "    vault = KeyVaults('Key Vault')\n"
            "    \n"
            "    webapp >> db\n"
            "    webapp >> vault\n"
            "```\n\n"
            "Your response must be executable Python code only."
        )

        # Try creating agent with tools first
        try:
            create_agent_task = agents_client.create_agent(
                model=MODEL_NAME,
                name=AGENT_NAME,
                instructions=instructions,
                tools=["code_interpreter"]  # Simplified format
            )
            
            if asyncio.iscoroutine(create_agent_task):
                agent = await create_agent_task
            else:
                agent = create_agent_task
                
        except Exception as e:
            logger.warning(f"Failed to create agent with tools: {e}")
            logger.info("Retrying without tools...")
            # Fallback: create agent without tools
            create_agent_task = agents_client.create_agent(
                model=MODEL_NAME,
                name=AGENT_NAME,
                instructions=instructions
            )
            
            if asyncio.iscoroutine(create_agent_task):
                agent = await create_agent_task
            else:
                agent = create_agent_task

        # Handle both object and dictionary formats for the created agent
        agent_id = agent.get("id") if isinstance(agent, dict) else getattr(agent, "id", None)
        _cached_agent_id = agent_id
        logger.info(f"Created new diagram agent: {agent_id}")
        return agent_id
    except Exception as e:
        logger.error(f"Error creating diagram agent: {e}")
        raise


async def generate_diagram_code(user_input: str) -> str:
    """
    Generate only the diagram code without rendering it.
    Used by enhanced diagram generator for validation workflow.
    """
    if not user_input or not user_input.strip():
        raise ValueError("No input provided for diagram generation.")
    
    if not PROJECT_ENDPOINT:
        raise ValueError("PROJECT_ENDPOINT not configured.")

    try:
        agents_client = get_diagram_agents_client()
        agent_id = await get_or_create_diagram_agent()

        logger.info(f"Starting diagram code generation for: {user_input[:100]}...")

        # Create thread
        thread_task = agents_client.threads.create()
        if asyncio.iscoroutine(thread_task):
            thread = await thread_task
        else:
            thread = thread_task
            
        thread_id = thread.get("id") if isinstance(thread, dict) else getattr(thread, "id", None)
        logger.info(f"Created thread: {thread_id}")

        # Create message
        message_task = agents_client.messages.create(
            thread_id=thread_id,
            role="user",
            content=f"""Please generate a diagram based on this architecture:

{user_input}

Use the `diagrams` Python library (https://diagrams.mingrammer.com).
Output ONLY executable Python code. Do NOT return markdown or explanations."""
        )
        
        if asyncio.iscoroutine(message_task):
            await message_task
        else:
            pass  # Message created

        logger.info("Starting diagram agent run...")
        
        # Create and process run
        run_task = agents_client.runs.create_and_process(thread_id=thread_id, agent_id=agent_id)
        if asyncio.iscoroutine(run_task):
            run = await run_task
        else:
            run = run_task
            
        run_status = run.get("status") if isinstance(run, dict) else getattr(run, "status", "unknown")
        logger.info(f"Diagram agent run completed: {run_status}")

        if run_status == "failed":
            last_error = run.get("last_error") if isinstance(run, dict) else getattr(run, "last_error", "Unknown error")
            raise Exception(f"Diagram agent failed: {last_error}")

        # Get messages
        messages_task = agents_client.messages.list(thread_id=thread_id, order="desc")
        if asyncio.iscoroutine(messages_task):
            messages = await messages_task
        else:
            messages = list(messages_task)

        # Find the assistant's response
        code = None
        for message in messages:
            message_role = message.get("role") if isinstance(message, dict) else getattr(message, "role", None)
            message_content = message.get("content") if isinstance(message, dict) else getattr(message, "content", None)
            
            if message_role == "assistant" and message_content:
                logger.info("Processing assistant message content...")
                logger.debug(f"Content type: {type(message_content)}")
                
                # Handle different content formats
                combined_text = ""
                if isinstance(message_content, str):
                    combined_text = message_content
                elif isinstance(message_content, list):
                    # Handle Azure AI response structure
                    for item in message_content:
                        if isinstance(item, dict):
                            if item.get("type") == "text":
                                text_obj = item.get("text", {})
                                if isinstance(text_obj, dict) and "value" in text_obj:
                                    combined_text += text_obj["value"]
                                elif isinstance(text_obj, str):
                                    combined_text += text_obj
                        elif hasattr(item, 'type') and hasattr(item, 'text'):
                            if item.type == "text" and hasattr(item.text, 'value'):
                                combined_text += item.text.value
                else:
                    logger.error(f"Unexpected message content type: {type(message_content)}")
                    continue

                if combined_text and combined_text.strip():
                    code = extract_code(combined_text)
                    logger.info(f"Successfully extracted diagram code ({len(code)} characters)")
                    break

        if not code:
            raise Exception("No diagram code returned by assistant.")

        return code

    except Exception as e:
        logger.error(f"Error in diagram code generation: {e}")
        raise


async def generate_diagram(user_input: str) -> str:
    """
    Generate diagram and return the URL (Azure Storage or local).
    This is the original function that generates code and renders it.
    """
    try:
        # Generate the code first
        code = await generate_diagram_code(user_input)

        # Generate UUID for filename 
        file_uuid = str(uuid.uuid4())
        filename = f"{file_uuid}.png"
        filepath = os.path.join("static", "diagrams", filename)
        
        # Pass the UUID to the render function so it can modify the diagram title
        render_code_to_image(code, filepath, file_uuid)

        # Upload to Azure Storage if available
        try:
            from .storage import upload_diagram
            diagram_url = await upload_diagram(filepath, filename)
            
            if diagram_url and diagram_url != filepath:
                # Successfully uploaded to Azure Storage
                logger.info(f"Diagram uploaded to Azure Storage: {diagram_url}")
                return diagram_url
            else:
                # Fallback to local path
                logger.info(f"Using local diagram path: /static/diagrams/{filename}")
                return f"/static/diagrams/{filename}"
                
        except Exception as e:
            logger.warning(f"Error uploading diagram to Azure Storage: {e}")
            return f"/static/diagrams/{filename}"

    except Exception as e:
        logger.error(f"Error in diagram generation: {e}")
        raise


def extract_code(content: str) -> str:
    """
    Extract the actual Python code from the assistant response,
    which may be inside triple backticks or plain text.
    """
    import re

    if not content or not content.strip():
        logger.debug("Content is empty or None")
        return ""

    logger.debug(f"Extracting code from content: {repr(content[:200])}...")

    # First: try to extract content inside triple backticks with python specifier
    code_blocks = re.findall(r"```python\n(.*?)```", content, re.DOTALL)
    if code_blocks:
        extracted = code_blocks[0].strip()
        logger.debug(f"Found python code block (pattern 1): {repr(extracted[:100])}...")
        return extracted
    
    # Second: try to extract content inside any triple backticks
    code_blocks = re.findall(r"```\n(.*?)```", content, re.DOTALL)
    if code_blocks:
        extracted = code_blocks[0].strip() 
        logger.debug(f"Found generic code block (pattern 2): {repr(extracted[:100])}...")
        return extracted

    # Third: try without requiring newline after backticks
    code_blocks = re.findall(r"```(?:python)?\s*(.*?)```", content, re.DOTALL)
    if code_blocks:
        extracted = code_blocks[0].strip()
        logger.debug(f"Found flexible code block (pattern 3): {repr(extracted[:100])}...")
        return extracted

    # Fourth: More aggressive pattern - capture everything between backticks
    code_blocks = re.findall(r"```.*?\n(.*?)```", content, re.DOTALL)
    if code_blocks:
        extracted = code_blocks[0].strip()
        logger.debug(f"Found aggressive code block (pattern 4): {repr(extracted[:100])}...")
        return extracted

    # Fallback: try to detect code inline (in case no markdown block is used)
    if "from diagrams" in content or "with Diagram" in content:
        logger.debug(f"Found inline code: {repr(content.strip()[:100])}...")
        return content.strip()

    logger.debug("No code patterns matched")
    return ""


def render_code_to_image(code: str, filepath: str, file_uuid: str):
    from diagrams import Diagram
    import os
    import re

    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Comprehensive import validation and fixing
        fixed_code = validate_and_fix_imports(code)
        
        # CRITICAL FIX: Replace the diagram title but keep it user-friendly
        # The UUID is only used for the filename, not the display title
        title_pattern = r'with Diagram\("([^"]+)"([^)]*)\):'
        
        def replace_title_keep_readable(match):
            original_title = match.group(1)
            params = match.group(2)
            
            # Keep the original title for display, but ensure the filename is UUID
            # The filename will be handled separately by changing directory and using UUID
            logger.debug(f"Keeping readable title '{original_title}' for display")
            
            # Ensure show=False is present to use UUID filename
            if 'show=False' not in params:
                if params.strip():
                    return f'with Diagram("{original_title}"{params}, show=False):'
                else:
                    return f'with Diagram("{original_title}", show=False):'
            else:
                return f'with Diagram("{original_title}"{params}):'
        
        fixed_code = re.sub(title_pattern, replace_title_keep_readable, fixed_code)
        
        logger.debug(f"Final code to execute:\n{fixed_code}")
        
        # Set up the working directory for diagrams
        original_cwd = os.getcwd()
        output_dir = os.path.dirname(filepath)
        
        try:
            # Change to the output directory temporarily
            os.chdir(output_dir)
            
            # Create a safe execution environment
            exec_globals = {
                "__file__": filepath,
                "__name__": "__main__",
                "Diagram": Diagram,
            }
            
            # Import all necessary diagrams modules
            try:
                import diagrams.azure.web
                import diagrams.azure.security  
                import diagrams.azure.database
                import diagrams.azure.network
                import diagrams.azure.storage
                import diagrams.azure.compute
                import diagrams.azure.general
                
                # Add modules to globals
                exec_globals.update({
                    'diagrams': diagrams,
                })
            except ImportError as e:
                logger.warning(f"Could not import some diagrams modules: {e}")
            
            # Execute the fixed code (filename will be based on working directory)
            exec(fixed_code, exec_globals)
            
            # After execution, find the created file and rename it to UUID
            png_files = [f for f in os.listdir('.') if f.endswith('.png')]
            if png_files:
                # Get the most recently created PNG file
                created_file = max(png_files, key=os.path.getctime)
                expected_file = f"{file_uuid}.png"
                
                if created_file != expected_file:
                    os.rename(created_file, expected_file)
                    logger.info(f"Renamed '{created_file}' to '{expected_file}'")
                else:
                    logger.info(f"Diagram created as '{expected_file}'")
            else:
                raise Exception("No PNG file was created")
                
        finally:
            # Always restore the original working directory
            os.chdir(original_cwd)
        
    except Exception as e:
        logger.error(f"Error executing diagram code: {e}")
        logger.debug(f"Code that failed:\n{fixed_code}")
        
        # Try to provide a helpful error message with available imports
        if "cannot import name" in str(e):
            try:
                # Try to show available imports for debugging
                import diagrams.azure.web
                import diagrams.azure.security
                import diagrams.azure.database
                import diagrams.azure.network
                import diagrams.azure.storage
                import diagrams.azure.compute
                import diagrams.azure.general                
                
                logger.debug("Available imports:")
                logger.debug(f"diagrams.azure.web: {[x for x in dir(diagrams.azure.web) if not x.startswith('_')]}")
                logger.debug(f"diagrams.azure.security: {[x for x in dir(diagrams.azure.security) if not x.startswith('_')]}")
                logger.debug(f"diagrams.azure.database: {[x for x in dir(diagrams.azure.database) if not x.startswith('_')]}")
                logger.debug(f"diagrams.azure.network: {[x for x in dir(diagrams.azure.network) if not x.startswith('_')]}")
                logger.debug(f"diagrams.azure.storage: {[x for x in dir(diagrams.azure.storage) if not x.startswith('_')]}")
                logger.debug(f"diagrams.azure.compute: {[x for x in dir(diagrams.azure.compute) if not x.startswith('_')]}")
                logger.debug(f"diagrams.azure.general: {[x for x in dir(diagrams.azure.general) if not x.startswith('_')]}")
            except Exception as debug_e:
                logger.debug(f"Could not gather debug info: {debug_e}")
                
        raise RuntimeError(f"Failed to render diagram: {e}")


def validate_and_fix_imports(code: str) -> str:
    """
    Validate and fix common import issues in diagrams code
    """
    import re
    
    # Define the correct mappings based on available imports
    AZURE_IMPORT_MAPPINGS = {
        # Web services
        'AppService': 'AppServices',
        'WebApp': 'AppServices', 
        'WebApps': 'AppServices',
        
        # Security
        'KeyVault': 'KeyVaults',
        
        # Database  
        'CosmosDb': 'CosmosDb',  # This one is correct
        'Database': 'SQLDatabases',
        'SqlDatabase': 'SQLDatabases',
        
        # Compute
        'FunctionApp': 'FunctionApps',
        'VirtualMachine': 'VirtualMachines',
        
        # Storage
        'StorageAccount': 'StorageAccounts',
        'BlobStorage': 'BlobStorage',  # This one is correct
        
        # Network
        'VirtualNetwork': 'VirtualNetworks',
        'LoadBalancer': 'LoadBalancers',
    }
    
    fixed_code = code
    
    # First, handle specific module fixes (identity -> security)
    specific_fixes = {
        'from diagrams.azure.identity import KeyVault': 'from diagrams.azure.security import KeyVaults as KeyVault',
        'from diagrams.azure.identity import KeyVaults': 'from diagrams.azure.security import KeyVaults',
    }
    
    for incorrect, correct in specific_fixes.items():
        if incorrect in fixed_code:
            logger.debug(f"Applying specific fix: {incorrect} -> {correct}")
            fixed_code = fixed_code.replace(incorrect, correct)
    
    # Fix the Diagram constructor - just ensure show=False is present
    diagram_pattern = r'with Diagram\("([^"]+)"([^)]*)\):'
    
    def fix_diagram_call(match):
        title = match.group(1)
        params = match.group(2)
        
        # Clean up any existing filename/outdir params
        params = re.sub(r',?\s*filename=\w+', '', params)
        params = re.sub(r',?\s*outdir=\w+', '', params)
        
        # Ensure show=False
        if 'show=' not in params:
            if params.strip() and not params.strip().endswith(','):
                params += ', '
            params += 'show=False'
        
        return f'with Diagram("{title}", {params.lstrip(", ")}):'
    
    fixed_code = re.sub(diagram_pattern, fix_diagram_call, fixed_code)
    
    # Now handle general import statement fixes (but skip ones already fixed by specific fixes)
    import_pattern = r'from diagrams\.azure\.(\w+) import ([\w, ]+)'
    
    def fix_import_line(match):
        module = match.group(1)  # e.g., 'web', 'security', etc.
        imports = match.group(2)  # e.g., 'AppService, KeyVault'
        
        # Skip if this line was already handled by specific fixes
        full_line = match.group(0)
        if 'as KeyVault' in full_line or module == 'security':
            return full_line  # Already fixed, don't modify
        
        # Split multiple imports
        import_list = [imp.strip() for imp in imports.split(',')]
        fixed_imports = []
        
        for imp in import_list:
            # Check if we have a mapping for this import
            if imp in AZURE_IMPORT_MAPPINGS:
                correct_name = AZURE_IMPORT_MAPPINGS[imp]
                if imp != correct_name:
                    # Use alias to maintain compatibility
                    fixed_imports.append(f"{correct_name} as {imp}")
                    logger.debug(f"Fixed import {imp} -> {correct_name} as {imp}")
                else:
                    fixed_imports.append(imp)
            else:
                # Keep the original import
                fixed_imports.append(imp)
        
        return f"from diagrams.azure.{module} import {', '.join(fixed_imports)}"
    
    
    # Apply the fixes
    fixed_code = re.sub(import_pattern, fix_import_line, fixed_code)
    
    return fixed_code