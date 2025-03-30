import uuid
import logging
import json
import re
import base64
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import traceback

from playwright.async_api import async_playwright, Browser, Page, Playwright
from src.services.llm_service import CloudflareChat, CloudflareModel
from src.models.glitch_agent import (
    BrowserAction,
    ActionType,
    CommandRequest,
    CommandResponse,
    ExecutionResult
)


class BrowserAutomationService:
    """Service for automating browser actions using natural language commands."""

    def __init__(self, api_key: str, account_id: str):
        """Initialize the BrowserAutomation service.
        
        Args:
            api_key: Cloudflare API key
            account_id: Cloudflare account ID
        """
        self.llm_service = CloudflareChat(
            api_key=api_key,
            account_id=account_id,
            model=CloudflareModel.LLAMA_3_70B_INSTRUCT
        )
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        logging.info("BrowserAutomation service initialized")

    async def start_browser(self, headless: bool = False) -> None:
        """Start a browser instance.
        
        Args:
            headless: Whether to run the browser in headless mode
        """
        if self.playwright is None:
            self.playwright = await async_playwright().start()
            
            # Configure browser launch options for Docker environment
            browser_launch_options = {
                "headless": headless,
                # Add Docker-specific browser arguments
                "args": [
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-gpu",
                    "--disable-software-rasterizer",
                ]
            }
            
            self.browser = await self.playwright.chromium.launch(**browser_launch_options)
            
            # Configure browser context with options suitable for automation
            context_options = {
                "viewport": {"width": 1280, "height": 720},
                "ignore_https_errors": True,
                "java_script_enabled": True,
            }
            
            self.context = await self.browser.new_context(**context_options)
            self.page = await self.context.new_page()
            
            # Set default timeout to 3 seconds
            self.page.set_default_timeout(30000)  # 3 seconds
            
            logging.info("Browser started in Docker environment")

    async def stop_browser(self) -> None:
        """Stop the browser instance."""
        if self.page:
            await self.page.close()
            self.page = None
        
        if self.context:
            await self.context.close()
            self.context = None
            
        if self.browser:
            await self.browser.close()
            self.browser = None
            
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
            
        logging.info("Browser stopped")

    def _create_nl_to_action_prompt(self, request: CommandRequest) -> str:
        """Create a prompt for the LLM to convert natural language to browser actions.
        
        Args:
            request: The command request
            
        Returns:
            Formatted prompt for the LLM
        """
        prompt = f"""
        Convert the following natural language command into a sequence of browser actions.
        
        Command: {request.command}
        """
        
        if request.context:
            prompt += f"""
            Additional context: {request.context}
            """
            
        prompt += """
        Use these action types:
        - navigate(url: str): Navigate to a URL
        - click(locator: str): Click on an element
        - fill(locator: str, text: str): Fill a form field
        - wait(time_ms: int): Wait for a specific time
        - submit(locator: str): Submit a form
        - press(key: str): Press a key
        - select(locator: str, value: str): Select an option from a dropdown
        - hover(locator: str): Hover over an element
        - screenshot(): Take a screenshot
        
        For locators, prioritize using specific selectors like:
        - id selectors (e.g., "#login-field")
        - input fields with specific attributes (e.g., "input[name='password']")
        - role selectors (e.g., "role:textbox[name='Username']")
        
        Avoid using generic text selectors that might match multiple elements.
        
        Return your response as a JSON array of actions. Each action should be an object with the action type and necessary parameters.
        
        Example output for "Log into GitHub":
        ```json
        [
          {"action": "navigate", "url": "https://github.com/login"},
          {"action": "fill", "locator": "input[name='login']", "text": "username"},
          {"action": "fill", "locator": "input[name='password']", "text": "password"},
          {"action": "click", "locator": "input[type='submit']"}
        ]
        ```
        
        Only respond with valid JSON. Do not include any other text in your response.
        """
        
        return prompt
        
    def _create_troubleshooting_prompt(self, action: BrowserAction, error_message: str, html_snippet: str) -> str:
        """Create a prompt for the LLM to troubleshoot automation issues.
        
        Args:
            action: The action that failed
            error_message: The error message
            html_snippet: HTML snippet of the current page
            
        Returns:
            Formatted prompt for the LLM
        """
        prompt = f"""
        I'm trying to automate a browser task but encountered an issue. Please help me fix it.
        
        Failed action:
        ```json
        {json.dumps(action.dict(), indent=2)}
        ```
        
        Error message:
        ```
        {error_message}
        ```
        
        Current page HTML snippet:
        ```html
        {html_snippet}
        ```
        
        Please analyze the issue and suggest a better approach. Specifically:
        1. Identify the problem with the current locator/action
        2. Suggest a better locator or alternative approach
        3. Return your suggestion as a JSON object with the same structure as the failed action, but with improved parameters
        
        For example, if a text locator matched multiple elements, suggest a more specific selector like an ID or attribute selector.
        
        Only respond with valid JSON for the fixed action. Do not include any other text in your response.
        """
        
        return prompt

    def _create_navigation_prompt(self, command: str) -> str:
        """Create a prompt for the LLM to extract just the navigation URL.
        
        Args:
            command: The natural language command
            
        Returns:
            Formatted prompt for the LLM
        """
        prompt = f"""
        Extract ONLY the URL to navigate to from this command: "{command}"
        
        If the command implies navigation to a website but doesn't specify a full URL, 
        provide a complete URL including https:// prefix.
        
        For example:
        - For "go to github", return "https://github.com"
        - For "search for cats on Google", return "https://google.com"
        - For "check CNN news", return "https://cnn.com"
        
        Return ONLY the URL, nothing else.
        """
        return prompt
        
    def _create_html_based_action_prompt(self, command: str, html_content: str, context: Optional[str] = None) -> str:
        """Create a prompt for the LLM to determine browser actions based on HTML content.
        
        Args:
            command: Natural language command
            html_content: HTML content of the current page
            context: Additional context for the command
            
        Returns:
            Formatted prompt for the LLM
        """
        # Get original size for logging
        original_size = len(html_content)
        logging.info(f"Original HTML size: {original_size} characters")

        # Clean HTML content by removing unnecessary parts
        # 1. Remove script tags and their contents
        html_content = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', html_content, flags=re.DOTALL)
        
        # 2. Remove style tags and their contents
        html_content = re.sub(r'<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>', '', html_content, flags=re.DOTALL)
        
        # 3. Remove comment tags
        html_content = re.sub(r'<!--.*?-->', '', html_content, flags=re.DOTALL)
        
        # 4. Remove meta tags
        html_content = re.sub(r'<meta\b[^>]*>', '', html_content)
        
        # 5. Remove link tags (CSS, favicon, etc.)
        html_content = re.sub(r'<link\b[^>]*>', '', html_content)
        
        # 6. Remove SVG content (often used for icons)
        html_content = re.sub(r'<svg\b[^<]*(?:(?!<\/svg>)<[^<]*)*<\/svg>', '', html_content, flags=re.DOTALL)
        
        # 7. Remove data attributes (data-* attributes often contain app-specific data)
        html_content = re.sub(r'\s+data-[a-zA-Z0-9_-]+="[^"]*"', '', html_content)
        
        # 8. Remove hidden elements
        html_content = re.sub(r'<[^>]*hidden[^>]*>.*?<\/[^>]*>', '', html_content, flags=re.DOTALL)
        html_content = re.sub(r'<[^>]*style="[^"]*display:\s*none[^"]*"[^>]*>.*?<\/[^>]*>', '', html_content, flags=re.DOTALL)
        
        # 9. Remove large blocks of whitespace
        html_content = re.sub(r'\s{2,}', ' ', html_content)
        
        # 10. Remove footer content (often not relevant for interactions)
        html_content = re.sub(r'<footer\b[^<]*(?:(?!<\/footer>)<[^<]*)*<\/footer>', '', html_content, flags=re.DOTALL)
        
        # Log the size reduction
        cleaned_size = len(html_content)
        reduction_percentage = ((original_size - cleaned_size) / original_size) * 100 if original_size > 0 else 0
        logging.info(f"Cleaned HTML size: {cleaned_size} characters (reduced by {reduction_percentage:.2f}%)")

        # Truncate HTML if still too long
        max_html_length = 15000
        if len(html_content) > max_html_length:
            logging.warning(f"HTML content is still too long after cleaning: {len(html_content)} characters")
            
            # Extract the most important parts: forms, interactive elements, and main content
            important_parts = []
            
            # Extract forms (likely to contain interactive elements)
            forms = re.findall(r'<form\b[^<]*(?:(?!<\/form>)<[^<]*)*<\/form>', html_content, flags=re.DOTALL)
            if forms:
                important_parts.extend(forms)
                logging.info(f"Extracted {len(forms)} forms")
            
            # Extract main content if present
            main_content = re.findall(r'<main\b[^<]*(?:(?!<\/main>)<[^<]*)*<\/main>', html_content, flags=re.DOTALL)
            if main_content:
                important_parts.extend(main_content)
                logging.info(f"Extracted main content section")
            
            # Extract article content if present
            article_content = re.findall(r'<article\b[^<]*(?:(?!<\/article>)<[^<]*)*<\/article>', html_content, flags=re.DOTALL)
            if article_content:
                important_parts.extend(article_content)
                logging.info(f"Extracted {len(article_content)} article sections")
            
            # If we have important parts, use them instead of truncating randomly
            if important_parts:
                html_content = "".join(important_parts)
                logging.info(f"Using extracted important parts: {len(html_content)} characters")
            
            # If still too long or no important parts found, truncate
            if len(html_content) > max_html_length:
                html_content = html_content[:max_html_length] + "... [truncated]"
                logging.warning(f"HTML content truncated to {max_html_length} characters")
        
        # Escape curly braces in HTML content to avoid f-string formatting issues
        html_content = html_content.replace("{", "{{").replace("}", "}}")
        
        prompt = f"""
        Based on the current webpage HTML and the user's command, determine the appropriate browser actions to execute.
        
        Command: {command}
        """
        
        if context:
            prompt += f"""
            Additional context: {context}
            """
            
        prompt += f"""
        Current webpage HTML:
        ```html
        {html_content}
        ```
        
        Use these action types:
        - click(locator: str): Click on an element
        - fill(locator: str, text: str): Fill a form field
        - wait(time_ms: int): Wait for a specific time
        - submit(locator: str): Submit a form
        - press(key: str): Press a key
        - select(locator: str, value: str): Select an option from a dropdown
        - hover(locator: str): Hover over an element
        - screenshot(): Take a screenshot
        
        For locators, prioritize using specific selectors like:
        - id selectors (e.g., "#login-field")
        - input fields with specific attributes (e.g., "input[name='password']")
        - role selectors (e.g., "role:textbox[name='Username']")
        
        Analyze the HTML carefully to find the most precise and reliable selectors.
        
        Return your response as a JSON array of actions. Each action should be an object with the action type and necessary parameters.
        
        Example output for filling a login form:
        ```json
        [
          {{"action": "fill", "locator": "input[name='login']", "text": "username"}},
          {{"action": "fill", "locator": "input[name='password']", "text": "password"}},
          {{"action": "click", "locator": "input[type='submit']"}}
        ]
        ```
        
        Only respond with valid JSON. Do not include any other text in your response.
        """
        
        return prompt
        
    async def get_current_page_html(self) -> str:
        """Get the full HTML content of the current page.
        
        Returns:
            HTML content of the current page
        """
        try:
            if not self.page:
                return "No active page"
            
            # Get the HTML content of the entire page
            html = await self.page.content()
            return html
                
        except Exception as e:
            logging.error(f"Error getting page HTML: {str(e)}")
            return f"Error getting HTML: {str(e)}"
            
    async def navigate_to_url(self, url: str) -> bool:
        """Navigate to a specific URL and return success status.
        
        Args:
            url: URL to navigate to
            
        Returns:
            True if navigation was successful, False otherwise
        """
        try:
            # Check if browser is active, if not start a new one
            if not self.page or not self.browser:
                logging.info("Browser not active, starting a new browser instance")
                await self.start_browser()
            
            # Check browser connection
            try:
                if self.page:
                    await self.page.evaluate("1 + 1")
            except Exception as browser_error:
                logging.warning(f"Browser connection check failed: {str(browser_error)}")
                # Reset browser state
                await self.stop_browser()
                await self.start_browser()
            
            # Navigate to the URL
            logging.info(f"Navigating to URL: {url}")
            await self.page.goto(url, wait_until="networkidle")
            return True
            
        except Exception as e:
            logging.error(f"Error navigating to URL {url}: {str(e)}")
            return False

    async def translate_command(self, request: CommandRequest) -> CommandResponse:
        """Translate a natural language command into browser actions.
        
        Args:
            request: The command request
            
        Returns:
            Response with actions to execute
        """
        # Generate a unique request ID
        request_id = str(uuid.uuid4())
        
        try:
            # Step 1: Get navigation URL from LLM
            logging.info("Step 1: Extracting navigation URL from command")
            navigation_prompt = self._create_navigation_prompt(request.command)
            
            # Call the LLM service to get the URL
            search_results = []
            url_response = self.llm_service.generate_answer(
                search_results=search_results,
                query=navigation_prompt
            )
            
            # Clean up the URL response
            url = url_response.strip().strip('"\'`').strip()
            
            # Ensure URL has http/https prefix
            if not url.startswith("http"):
                url = "https://" + url
                
            logging.info(f"Extracted URL: {url}")
            
            # Create navigation action
            navigation_action = BrowserAction(
                action=ActionType.NAVIGATE,
                url=url
            )
            
            # Step 2: Navigate to the URL
            logging.info("Step 2: Navigating to the URL")
            navigation_success = await self.navigate_to_url(url)
            
            if not navigation_success:
                raise ValueError(f"Failed to navigate to {url}")
                
            # Step 3: Get the HTML content
            logging.info("Step 3: Getting HTML content")
            html_content = await self.get_current_page_html()
            
            if html_content == "No active page" or html_content.startswith("Error getting HTML"):
                raise ValueError("Failed to get HTML content")
                
            # Step 4: Determine actions from HTML content
            logging.info("Step 4: Determining actions from HTML content")
            html_prompt = self._create_html_based_action_prompt(
                command=request.command,
                html_content=html_content,
                context=request.context
            )
            
            # Call the LLM service to get actions
            html_response = self.llm_service.generate_answer(
                search_results=search_results,
                query=html_prompt
            )
            
            # Parse the LLM response
            parsed_actions = self._parse_llm_response(html_response)
            
            # Convert the parsed actions to BrowserAction objects
            actions = []
            
            # First add the navigation action
            # actions.append(navigation_action)
            
            # Then add the HTML-based actions
            for action_data in parsed_actions:
                try:
                    # Ensure the action type is valid
                    action_type = ActionType(action_data.get("action", ""))
                    
                    # Skip navigation actions as we've already navigated
                    if action_type == ActionType.NAVIGATE:
                        continue
                    
                    # Create the BrowserAction object
                    action = BrowserAction(
                        action=action_type,
                        locator=action_data.get("locator"),
                        url=action_data.get("url"),
                        text=action_data.get("text"),
                        time_ms=action_data.get("time_ms"),
                        key=action_data.get("key"),
                        value=action_data.get("value")
                    )
                    actions.append(action)
                    logging.info(f"Parsed action: {action}")
                except (ValueError, KeyError) as e:
                    logging.warning(f"Skipping invalid action data: {str(e)}")
            
            # Create the response
            return CommandResponse(
                request_id=request_id,
                actions=actions,
                status="ready",
                message="Command translated successfully with HTML-based actions",
                created_at=datetime.now()
            )
            
        except Exception as e:
            print(traceback.format_exc())
            logging.error(f"Error in command translation: {str(e)} {traceback.format_exc()}")
            # Return an error response
            return CommandResponse(
                request_id=request_id,
                actions=[],
                status="error",
                message=f"Error during translation: {str(e)}",
                created_at=datetime.now()
            )
            
    def _parse_llm_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse the LLM response into a list of actions.
        
        Args:
            response: The raw response from the LLM
            
        Returns:
            List of parsed actions
        """
        # Try to extract JSON from the response
        json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # If no JSON code block, try to find any JSON-like structure
            json_str = re.search(r'(\[.*\])', response, re.DOTALL)
            if json_str:
                json_str = json_str.group(1)
            else:
                json_str = response
        
        try:
            # Clean up the string and parse as JSON
            json_str = json_str.strip()
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse LLM response as JSON: {str(e)}")
            # Return a default structure if parsing fails
            return []
            
    def _parse_troubleshooting_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM troubleshooting response.
        
        Args:
            response: The raw response from the LLM
            
        Returns:
            Parsed action data
        """
        # Try to extract JSON from the response
        json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # If no JSON code block, try to find any JSON-like structure
            json_str = re.search(r'({.*})', response, re.DOTALL)
            if json_str:
                json_str = json_str.group(1)
            else:
                json_str = response
        
        try:
            # Clean up the string and parse as JSON
            json_str = json_str.strip()
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse troubleshooting response as JSON: {str(e)}")
            # Return an empty dict if parsing fails
            return {}

    async def troubleshoot_action(self, action: BrowserAction, error_message: str) -> BrowserAction:
        """Use LLM to troubleshoot and fix a failed action.
        
        Args:
            action: The action that failed
            error_message: The error message
            
        Returns:
            Improved action
        """
        try:
            # Check if browser connection is still active
            if not self.page or not self.browser:
                logging.warning("Browser connection lost, cannot troubleshoot. Returning original action.")
                return action
                
            # Check if browser is still connected by attempting a simple operation
            try:
                await self.page.evaluate("1 + 1")
            except Exception as browser_error:
                logging.warning(f"Browser connection check failed: {str(browser_error)}")
                # Reset browser state
                await self.stop_browser()
                await self.start_browser()
                return action
            
            # Get HTML snippet of the current page for context
            html_snippet = await self._get_page_html_snippet()
            
            # Create the troubleshooting prompt
            prompt = self._create_troubleshooting_prompt(action, error_message, html_snippet)
            
            # Call the LLM service
            search_results = []  # No search results needed for this use case
            llm_response = self.llm_service.generate_answer(
                search_results=search_results,
                query=prompt
            )
            
            # Parse the troubleshooting response
            fixed_action_data = self._parse_troubleshooting_response(llm_response)
            
            if not fixed_action_data:
                logging.warning("LLM troubleshooting didn't return valid action data")
                return action  # Return the original action if troubleshooting failed
            
            # Create a new BrowserAction with the fixed data
            try:
                # Ensure the action type is valid
                action_type = ActionType(fixed_action_data.get("action", action.action))
                
                # Create the improved BrowserAction
                improved_action = BrowserAction(
                    action=action_type,
                    locator=fixed_action_data.get("locator", action.locator),
                    url=fixed_action_data.get("url", action.url),
                    text=fixed_action_data.get("text", action.text),
                    time_ms=fixed_action_data.get("time_ms", action.time_ms),
                    key=fixed_action_data.get("key", action.key),
                    value=fixed_action_data.get("value", action.value)
                )
                
                logging.info(f"LLM suggested improved action: {improved_action}")
                return improved_action
                
            except (ValueError, KeyError) as e:
                logging.warning(f"Invalid improved action data: {str(e)}")
                return action  # Return the original action if creating the improved action failed
            
        except Exception as e:
            logging.error(f"Error in action troubleshooting: {str(e)}")
            return action  # Return the original action if troubleshooting failed
            
    async def _get_page_html_snippet(self, max_length: int = 5000) -> str:
        """Get a snippet of the current page's HTML.
        
        Args:
            max_length: Maximum length of the HTML snippet
            
        Returns:
            HTML snippet
        """
        try:
            if not self.page:
                return "No active page"
            
            # Check if browser is still connected
            try:
                # Get the HTML content of the body
                html = await self.page.evaluate("document.body.innerHTML")
                
                # Truncate if too long
                if len(html) > max_length:
                    html = html[:max_length] + "... [truncated]"
                    
                return html
            except Exception as e:
                logging.warning(f"Failed to get page HTML, browser may be disconnected: {str(e)}")
                return f"Browser disconnected: {str(e)}"
                
        except Exception as e:
            logging.error(f"Error getting page HTML: {str(e)}")
            return f"Error getting HTML: {str(e)}"
            
    async def execute_actions(self, actions: List[BrowserAction], request_id: str) -> ExecutionResult:
        """Execute a list of browser actions.
        
        Args:
            actions: List of actions to execute
            request_id: Unique identifier for the request
            
        Returns:
            Result of the execution
        """
        # Initialize result
        result = ExecutionResult(
            request_id=request_id,
            success=True,
            message="Actions executed successfully",
            completed_at=datetime.now()
        )
        
        try:
            # Check if browser is active, if not start a new one
            if not self.page or not self.browser:
                logging.info("Browser not active, starting a new browser instance")
                await self.start_browser()
            
            # Check browser connection by attempting a simple operation
            try:
                if self.page:
                    await self.page.evaluate("1 + 1")
            except Exception as browser_error:
                logging.warning(f"Browser connection check failed: {str(browser_error)}")
                # Reset browser state
                await self.stop_browser()
                await self.start_browser()
            
            for i, action in enumerate(actions):
                logging.info(f"Executing action {i+1}/{len(actions)}: {action.action}")
                
                # Track retries for this action
                retries = 0
                max_retries = 2  # Maximum number of troubleshooting attempts
                
                while retries <= max_retries:
                    try:
                        # Check browser connection before each action
                        if not self.page or not self.browser:
                            logging.warning("Browser connection lost during execution, restarting browser")
                            await self.start_browser()
                            
                        if action.action == ActionType.NAVIGATE:
                            if not action.url:
                                raise ValueError("URL is required for navigate action")
                            await self.page.goto(action.url, wait_until="networkidle")
                            break  # Success, exit retry loop
                            
                        elif action.action == ActionType.CLICK:
                            if not action.locator:
                                raise ValueError("Locator is required for click action")
                            
                            # Handle different locator formats
                            await self._handle_click(action.locator)
                            break  # Success, exit retry loop
                            
                        elif action.action == ActionType.FILL:
                            if not action.locator or action.text is None:
                                raise ValueError("Locator and text are required for fill action")
                            
                            # Handle different locator formats with special handling for common form fields
                            await self._handle_fill(action.locator, action.text)
                            break  # Success, exit retry loop
                            
                        elif action.action == ActionType.WAIT:
                            if action.time_ms:
                                await asyncio.sleep(action.time_ms / 1000)  # Convert ms to seconds
                            else:
                                # Default wait time
                                await asyncio.sleep(1)
                            break  # Success, exit retry loop
                            
                        elif action.action == ActionType.SUBMIT:
                            if not action.locator:
                                raise ValueError("Locator is required for submit action")
                            await self.page.locator(action.locator).evaluate("form => form.submit()")
                            break  # Success, exit retry loop
                            
                        elif action.action == ActionType.PRESS:
                            if not action.key:
                                raise ValueError("Key is required for press action")
                            await self.page.keyboard.press(action.key)
                            break  # Success, exit retry loop
                            
                        elif action.action == ActionType.SELECT:
                            if not action.locator or not action.value:
                                raise ValueError("Locator and value are required for select action")
                            await self.page.locator(action.locator).select_option(value=action.value)
                            break  # Success, exit retry loop
                            
                        elif action.action == ActionType.HOVER:
                            if not action.locator:
                                raise ValueError("Locator is required for hover action")
                            await self.page.locator(action.locator).hover()
                            break  # Success, exit retry loop
                            
                        elif action.action == ActionType.SCREENSHOT:
                            # Take a screenshot and encode it as base64
                            screenshot_bytes = await self.page.screenshot()
                            result.screenshot = base64.b64encode(screenshot_bytes).decode('utf-8')
                            break  # Success, exit retry loop
                            
                        elif action.action == ActionType.EXTRACT:
                            # This would be implemented in Level 2
                            break  # Success, exit retry loop
                    
                    except Exception as e:
                        error_message = str(e)
                        logging.warning(f"Action failed (attempt {retries+1}/{max_retries+1}): {error_message}")
                        
                        # Check if browser is still connected
                        browser_connected = True
                        try:
                            if self.page:
                                await self.page.evaluate("1 + 1")
                            else:
                                browser_connected = False
                        except Exception:
                            browser_connected = False
                            
                        # If browser is disconnected, try to restart it
                        if not browser_connected:
                            logging.warning("Browser connection lost during retry, restarting browser")
                            await self.stop_browser()
                            await self.start_browser()
                            
                            # Skip troubleshooting if browser was disconnected
                            retries += 1
                            continue
                        
                        # If we've reached max retries, re-raise the exception
                        if retries >= max_retries:
                            raise
                        
                        # Use LLM to troubleshoot the action
                        logging.info(f"Using LLM to troubleshoot action: {action}")
                        improved_action = await self.troubleshoot_action(action, error_message)
                        
                        # Update the action with the improved version for the next attempt
                        action = improved_action
                        retries += 1
                        
                        # Wait a bit before retrying
                        await asyncio.sleep(1)
                
                # Wait a bit after each action for the page to update
                await asyncio.sleep(0.5)
                
            # Take a final screenshot
            try:
                if self.page:
                    screenshot_bytes = await self.page.screenshot()
                    result.screenshot = base64.b64encode(screenshot_bytes).decode('utf-8')
            except Exception as screenshot_error:
                logging.error(f"Failed to take final screenshot: {str(screenshot_error)}")
            
        except Exception as e:
            logging.error(f"Error executing actions: {str(e)}")
            result.success = False
            result.message = "Error executing actions"
            result.error = str(e)
            
            # Try to take a screenshot of the error state
            try:
                if self.page:
                    screenshot_bytes = await self.page.screenshot()
                    result.screenshot = base64.b64encode(screenshot_bytes).decode('utf-8')
            except Exception as screenshot_error:
                logging.error(f"Failed to take error screenshot: {str(screenshot_error)}")
            
        return result

    async def _handle_click(self, locator: str) -> None:
        """Handle click action with improved locator handling"""
        try:
            # First try with standard locator but using .first to avoid strict mode violations
            await self.page.locator(locator).first.click(timeout=3000)
            logging.info(f"Successfully clicked first element matching: {locator}")
            return
        except Exception as e:
            logging.warning(f"Standard click failed: {str(e)}")
            
            # Check if this is a strict mode violation (multiple elements found)
            if "strict mode violation" in str(e) and "resolved to" in str(e):
                try:
                    # Extract the count of elements from the error message
                    count_match = re.search(r'resolved to (\d+) elements', str(e))
                    if count_match:
                        count = int(count_match.group(1))
                        logging.info(f"Strict mode violation: Found {count} elements matching {locator}")
                        
                        # Try clicking the first visible element
                        logging.info(f"Attempting to click the first visible element matching: {locator}")
                        elements = await self.page.locator(locator).all()
                        
                        for i, element in enumerate(elements):
                            try:
                                # Check if element is visible
                                is_visible = await element.is_visible()
                                if is_visible:
                                    logging.info(f"Clicking visible element {i+1} of {len(elements)}")
                                    await element.click(timeout=3000)
                                    return
                            except Exception as elem_error:
                                logging.warning(f"Failed to click element {i+1}: {str(elem_error)}")
                                continue
                except Exception as multi_error:
                    logging.warning(f"Failed to handle multiple elements: {str(multi_error)}")
            
            # Try different locator strategies
            if locator.startswith("role:"):
                role_match = re.match(r'role:(\w+)(?:\[name=[\'"]([^\'"]+)[\'"]\])?', locator)
                if role_match:
                    role, name = role_match.groups()
                    try:
                        if name:
                            # Use get_by_role with name parameter
                            await self.page.get_by_role(role, name=name).first.click(timeout=3000)
                        else:
                            # Use get_by_role without name parameter
                            await self.page.get_by_role(role).first.click(timeout=3000)
                        logging.info(f"Successfully clicked using role selector: {role}")
                        return
                    except Exception as role_error:
                        logging.warning(f"Role-based click failed: {str(role_error)}")
            
            # Try by text
            if locator.startswith("text=") or locator.startswith("text:"):
                text = locator.split("=", 1)[1].strip("'\"") if "=" in locator else locator.split(":", 1)[1].strip("'\"")
                try:
                    # Use get_by_text
                    await self.page.get_by_text(text).first.click(timeout=3000)
                    logging.info(f"Successfully clicked using text: {text}")
                    return
                except Exception as text_error:
                    logging.warning(f"Text-based click failed: {str(text_error)}")
            
            # Try by link text for anchor elements
            if locator.startswith("a[href") or "href" in locator:
                # Try to extract the link text from the page
                try:
                    # Get all links that match the href pattern
                    href_pattern = re.search(r'href=[\'"]([^\'"]+)[\'"]', locator)
                    if href_pattern:
                        href_value = href_pattern.group(1)
                        logging.info(f"Trying to find link with href: {href_value}")
                        
                        # Try clicking by href directly
                        await self.page.get_by_role("link", exact=False).filter(has_text=href_value).first.click(timeout=3000)
                        logging.info(f"Successfully clicked link with href: {href_value}")
                        return
                except Exception as href_error:
                    logging.warning(f"Href-based click failed: {str(href_error)}")
            
            # Try common button selectors for login forms
            if "login" in locator.lower() or "sign in" in locator.lower():
                for selector in [
                    "input[type='submit']", 
                    "button[type='submit']",
                    "button.btn-primary",
                    ".btn-login",
                    ".btn-signin"
                ]:
                    try:
                        await self.page.locator(selector).first.click(timeout=3000)
                        logging.info(f"Successfully clicked using common button selector: {selector}")
                        return
                    except Exception:
                        continue
            
            # If all else fails, try with nth elements
            # This handles cases where there are multiple identical elements
            try:
                elements_count = await self.page.locator(locator).count()
                logging.info(f"Found {elements_count} elements matching: {locator}")
                
                if elements_count > 0:
                    # Try each element one by one
                    for i in range(elements_count):
                        try:
                            await self.page.locator(locator).nth(i).click(timeout=3000)
                            logging.info(f"Successfully clicked element {i+1} of {elements_count}")
                            return
                        except Exception as nth_error:
                            logging.warning(f"Failed to click element {i+1}: {str(nth_error)}")
                            # Continue trying the next element
                            continue
            except Exception as count_error:
                logging.warning(f"Failed to count elements: {str(count_error)}")
            
            # Last resort: force click using JavaScript
            # try:
            #     logging.info("Attempting to force click using JavaScript")
            #     await self.page.evaluate(f"""
            #         (function() {{
            #             const elements = document.querySelectorAll('{locator.replace("'", "\\'")}');
            #             if (elements.length > 0) {{
            #                 elements[0].click();
            #                 return true;
            #             }}
            #             return false;
            #         }})()
            #     """)
            #     logging.info("JavaScript click executed")
                return
            except Exception as js_error:
                logging.error(f"JavaScript click failed: {str(js_error)}")
                # Re-raise the original exception
                raise
    
    async def _handle_fill(self, locator: str, text: str) -> None:
        """Handle fill action with improved locator handling for form fields"""
        try:
            # First try with standard locator
            await self.page.locator(locator).fill(text, timeout=3000)
            return
        except Exception as e:
            logging.warning(f"Standard fill failed: {str(e)}")
            
            # Special handling for common form fields
            # Check if this is a username/email field
            if "username" in locator.lower() or "login" in locator.lower() or "email" in locator.lower():
                for selector in [
                    "input[name='login']",
                    "input[name='username']", 
                    "input[name='email']",
                    "input[id='login_field']",
                    "#login_field"
                ]:
                    try:
                        await self.page.locator(selector).fill(text, timeout=3000)
                        return
                    except Exception:
                        continue
            
            # Check if this is a password field
            if "password" in locator.lower():
                for selector in [
                    "input[name='password']",
                    "input[type='password']",
                    "#password"
                ]:
                    try:
                        await self.page.locator(selector).fill(text, timeout=3000)
                        return
                    except Exception:
                        continue
            
            # Try different locator strategies
            if locator.startswith("role:"):
                role_match = re.match(r'role:(\w+)(?:\[name=[\'"]([^\'"]+)[\'"]\])?', locator)
                if role_match:
                    role, name = role_match.groups()
                    try:
                        if name:
                            # Use get_by_role with name parameter
                            await self.page.get_by_role(role, name=name).first.fill(text, timeout=3000)
                        else:
                            # Use get_by_role without name parameter
                            await self.page.get_by_role(role).first.fill(text, timeout=3000)
                        return
                    except Exception:
                        pass
            
            # Try by label text for form fields
            if locator.startswith("text=") or locator.startswith("text:"):
                label_text = locator.split("=", 1)[1].strip("'\"") if "=" in locator else locator.split(":", 1)[1].strip("'\"")
                try:
                    # Find the label element
                    label = await self.page.get_by_text(label_text, exact=True).first.element_handle()
                    # Get the 'for' attribute which should point to the input field id
                    for_attr = await label.get_attribute("for")
                    if for_attr:
                        # Use the for attribute to find the input
                        await self.page.locator(f"#{for_attr}").fill(text, timeout=3000)
                        return
                except Exception:
                    pass
            
            # If all else fails, try with first matching element
            await self.page.locator(locator).first.fill(text, timeout=3000)
