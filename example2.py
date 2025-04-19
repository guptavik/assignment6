# basic import 
from mcp.server.fastmcp import FastMCP, Image
from mcp.server.fastmcp.prompts import base
from mcp.types import TextContent
from mcp import types
from PIL import Image as PILImage
import math
import sys
from pywinauto.application import Application
import win32gui
import win32con
import time
from win32api import GetSystemMetrics
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
from dotenv import load_dotenv
import base64
from email.mime.application import MIMEApplication

# instantiate an MCP server client
mcp = FastMCP("Calculator")


# Load environment variables from .env file
load_dotenv()

# If modifying these scopes, delete the file token.pickle.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.modify'
]

# DEFINE TOOLS
def get_gmail_service():
    """Get or create Gmail API service."""
    creds = None
    # The file token.pickle stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('gmail', 'v1', credentials=creds)

def create_message(sender, to, subject, message_text):
    """Create a message for an email."""
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')}

@mcp.tool()
def send_email(emailto: str, subject: str, body: str) -> str:
    """
    Send email to a specific email address.
    
    Args:
        emailto (str): The email address to send the email to
        subject (str): The subject of the email
        body (str): The body of the email
    
    Returns:
        str: Status of the email sending operation
    """

    try:
        # Get sender email from environment variables
        sender_email = os.getenv('EMAIL_ADDRESS')
        
        if not sender_email:
            raise ValueError("Missing email address. Please check your .env file.")
        
        # Format the phone number (remove any non-digits)
        #phone_number = ''.join(filter(str.isdigit, phone_number))
        
    
        # Get Gmail service
        service = get_gmail_service()
        
        # Create the message
        message = create_message(
            sender_email,
            emailto,
            subject,
            body
        )
        
        # Send the message
        sent_message = service.users().messages().send(
            userId='me',
            body=message
        ).execute()
        
        #print(f"Message sent successfully to {phone_number}@tmomail.net")
        return f"Email sent successfully to {emailto}"
        
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return f"Error sending email: {str(e)}"




#addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    print("CALLED: add(a: int, b: int) -> int:")
    return int(a + b)

@mcp.tool()
def add_list(l: list) -> int:
    """Add all numbers in a list"""
    print("CALLED: add(l: list) -> int:")
    return sum(l)

# subtraction tool
@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Subtract two numbers"""
    print("CALLED: subtract(a: int, b: int) -> int:")
    return int(a - b)

# multiplication tool
@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    print("CALLED: multiply(a: int, b: int) -> int:")
    return int(a * b)

#  division tool
@mcp.tool() 
def divide(a: int, b: int) -> float:
    """Divide two numbers"""
    print("CALLED: divide(a: int, b: int) -> float:")
    return float(a / b)

# power tool
@mcp.tool()
def power(a: int, b: int) -> int:
    """Power of two numbers"""
    print("CALLED: power(a: int, b: int) -> int:")
    return int(a ** b)

# square root tool
@mcp.tool()
def sqrt(a: int) -> float:
    """Square root of a number"""
    print("CALLED: sqrt(a: int) -> float:")
    return float(a ** 0.5)

# cube root tool
@mcp.tool()
def cbrt(a: int) -> float:
    """Cube root of a number"""
    print("CALLED: cbrt(a: int) -> float:")
    return float(a ** (1/3))

# factorial tool
@mcp.tool()
def factorial(a: int) -> int:
    """factorial of a number"""
    print("CALLED: factorial(a: int) -> int:")
    return int(math.factorial(a))

# log tool
@mcp.tool()
def log(a: int) -> float:
    """log of a number"""
    print("CALLED: log(a: int) -> float:")
    return float(math.log(a))

# remainder tool
@mcp.tool()
def remainder(a: int, b: int) -> int:
    """remainder of two numbers divison"""
    print("CALLED: remainder(a: int, b: int) -> int:")
    return int(a % b)

# sin tool
@mcp.tool()
def sin(a: int) -> float:
    """sin of a number"""
    print("CALLED: sin(a: int) -> float:")
    return float(math.sin(a))

# cos tool
@mcp.tool()
def cos(a: int) -> float:
    """cos of a number"""
    print("CALLED: cos(a: int) -> float:")
    return float(math.cos(a))

# tan tool
@mcp.tool()
def tan(a: int) -> float:
    """tan of a number"""
    print("CALLED: tan(a: int) -> float:")
    return float(math.tan(a))

# mine tool
@mcp.tool()
def mine(a: int, b: int) -> int:
    """special mining tool"""
    print("CALLED: mine(a: int, b: int) -> int:")
    return int(a - b - b)

@mcp.tool()
def create_thumbnail(image_path: str) -> Image:
    """Create a thumbnail from an image"""
    print("CALLED: create_thumbnail(image_path: str) -> Image:")
    img = PILImage.open(image_path)
    img.thumbnail((100, 100))
    return Image(data=img.tobytes(), format="png")

@mcp.tool()
def strings_to_chars_to_int(string: str) -> list[int]:
    """Return the ASCII values of the characters in a word"""
    print("CALLED: strings_to_chars_to_int(string: str) -> list[int]:")
    return [int(ord(char)) for char in string]

@mcp.tool()
def int_list_to_exponential_sum(int_list: list) -> float:
    """Return sum of exponentials of numbers in a list"""
    print("CALLED: int_list_to_exponential_sum(int_list: list) -> float:")
    return sum(math.exp(i) for i in int_list)

@mcp.tool()
def fibonacci_numbers(n: int) -> list:
    """Return the first n Fibonacci Numbers"""
    print("CALLED: fibonacci_numbers(n: int) -> list:")
    if n <= 0:
        return []
    fib_sequence = [0, 1]
    for _ in range(2, n):
        fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])
    return fib_sequence[:n]


@mcp.tool()
def send_email(emailto: str, subject: str, body: str) -> dict:
    """Send an email"""
    print(f"Sending email to {emailto} with subject {subject} and body {body}")
    return "Email sent successfully"


@mcp.tool()
async def paint_the_number_in_rectangle(number: str, x1: int, y1: int, x2: int, y2: int) -> dict:
    """Paint the number in the rectangle"""
    print(f"Painting the number {number} in the rectangle with coordinates ({x1}, {y1}, {x2}, {y2})")
    
    result = await open_paint()

    # Wait longer for Paint to be fully maximized
    time.sleep(1)

    # Draw a rectangle
    result = await draw_rectangle(x1, y1, x2, y2)
    
    #print(result.content[0].text)

    time.sleep(1)

    # Draw rectangle and add text
    result = await add_text_in_paint(str(number))

    return "Number painted successfully"


@mcp.tool()
async def draw_rectangle(x1: int, y1: int, x2: int, y2: int) -> dict:
    """Draw a rectangle in Paint from (x1,y1) to (x2,y2)"""
    global paint_app
    try:
        if not paint_app:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="Paint is not open. Please call open_paint first."
                    )
                ]
            }
        
        # Get the Paint window
        paint_window = paint_app.window(class_name='MSPaintApp')
        
        # Get primary monitor width to adjust coordinates
        primary_width = GetSystemMetrics(0)
        
        # Ensure Paint window is active
        if not paint_window.has_focus():
            paint_window.set_focus()
            time.sleep(0.5)
        
        # Select pencil tool first
        # paint_window.type_keys('TP')
        #time.sleep(0.2)
        
        # Then select rectangle shape tool at specific coordinates
        paint_window.click_input(coords=(536, 82))
        time.sleep(1)
        
        # Get the canvas area
        canvas = paint_window.child_window(class_name='MSPaintView')
        
        # Draw rectangle - coordinates should already be relative to the Paint window
        # No need to add primary_width since we're clicking within the Paint window
        # canvas.press_mouse_input(coords=(x1+2560, y1))
        # canvas.move_mouse_input(coords=(x2+2560, y2))
        # canvas.release_mouse_input(coords=(x2+2560, y2))

        # Draw rectangle - coordinates should already be relative to the Paint window
        paint_window.click_input(coords=(x1, y1))

        canvas.press_mouse_input(coords=(x1, y1))
        canvas.move_mouse_input(coords=(x2, y2))
        canvas.release_mouse_input(coords=(x2, y2))


        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Rectangle drawn from ({x1},{y1}) to ({x2},{y2})"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error drawing rectangle: {str(e)}"
                )
            ]
        }

@mcp.tool()
async def add_text_in_paint(text: str) -> dict:
    """Add text in Paint"""
    global paint_app
    try:
        if not paint_app:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="Paint is not open. Please call open_paint first."
                    )
                ]
            }
        
        # Get the Paint window
        paint_window = paint_app.window(class_name='MSPaintApp')
        
        # Ensure Paint window is active
        if not paint_window.has_focus():
            paint_window.set_focus()
            time.sleep(0.5)
        
        # Click on the Rectangle tool
        paint_window.click_input(coords=(780, 380))
        time.sleep(0.5)
        
        # Get the canvas area
        canvas = paint_window.child_window(class_name='MSPaintView')
        
        # Select text tool using keyboard shortcuts
        paint_window.type_keys('t')
        time.sleep(0.5)
        paint_window.type_keys('x')
        time.sleep(0.5)
        
        # Click where to start typing
        canvas.click_input(coords=(780, 380))
        time.sleep(0.5)
        
        # Type the text passed from client
        paint_window.type_keys(text)
        #paint_window.type_keys('Hello')
        time.sleep(0.5)
        
        # Click to exit text mode
        canvas.click_input(coords=(1050, 800))
        
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Text:'{text}' added successfully"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )
            ]
        }

@mcp.tool()
async def open_paint() -> dict:
    """Open Microsoft Paint maximized on primary monitor"""
    global paint_app
    try:
        paint_app = Application().start('mspaint.exe')
        time.sleep(0.2)
        
        # Get the Paint window
        paint_window = paint_app.window(class_name='MSPaintApp')
        
        # Get primary monitor width
        primary_width = GetSystemMetrics(0)
        print(f"\n\nPrimary width: {primary_width}")
        
        # First move to primary monitor without specifying size
        win32gui.SetWindowPos(
            paint_window.handle,
            win32con.HWND_TOP,
            #primary_width + 1, 0,  # Position it on secondary monitor
            0, 0,
            0, 0,  # Let Windows handle the size
            win32con.SWP_NOSIZE  # Don't change the size
        )
        
        # Now maximize the window
        win32gui.ShowWindow(paint_window.handle, win32con.SW_MAXIMIZE)
        time.sleep(0.2)

        
        return {
            "content": [
                TextContent(
                    type="text",
                    text="Paint opened successfully on primary monitor and maximized"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error opening Paint: {str(e)}"
                )
            ]
        }
# DEFINE RESOURCES

# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    print("CALLED: get_greeting(name: str) -> str:")
    return f"Hello, {name}!"


# DEFINE AVAILABLE PROMPTS
@mcp.prompt()
def review_code(code: str) -> str:
    return f"Please review this code:\n\n{code}"
    print("CALLED: review_code(code: str) -> str:")


@mcp.prompt()
def debug_error(error: str) -> list[base.Message]:
    return [
        base.UserMessage("I'm seeing this error:"),
        base.UserMessage(error),
        base.AssistantMessage("I'll help debug that. What have you tried so far?"),
    ]


@mcp.tool()
def show_reasoning(steps: list) -> TextContent:
    """Show the step-by-step reasoning process"""
    console.print("[blue]FUNCTION CALL:[/blue] show_reasoning()")
    for i, step in enumerate(steps, 1):
        console.print(Panel(
            f"{step}",
            title=f"Step {i}",
            border_style="cyan"
        ))
    return TextContent(
        type="text",
        text="Reasoning shown"
    )

@mcp.tool()
def calculate(expression: str) -> TextContent:
    """Calculate the result of an expression"""
    console.print("[blue]FUNCTION CALL:[/blue] calculate()")
    console.print(f"[blue]Expression:[/blue] {expression}")
    try:
        result = eval(expression)
        console.print(f"[green]Result:[/green] {result}")
        return TextContent(
            type="text",
            text=str(result)
        )
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        return TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )

@mcp.tool()
def verify(expression: str, expected: float) -> TextContent:
    """Verify if a calculation is correct"""
    console.print("[blue]FUNCTION CALL:[/blue] verify()")
    console.print(f"[blue]Verifying:[/blue] {expression} = {expected}")
    try:
        actual = float(eval(expression))
        is_correct = abs(actual - float(expected)) < 1e-10
        
        if is_correct:
            console.print(f"[green]✓ Correct! {expression} = {expected}[/green]")
        else:
            console.print(f"[red]✗ Incorrect! {expression} should be {actual}, got {expected}[/red]")
            
        return TextContent(
            type="text",
            text=str(is_correct)
        )
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        return TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )

if __name__ == "__main__":
    # Check if running with mcp dev command
    print("STARTING")
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()  # Run without transport for dev server
    else:
        mcp.run(transport="stdio")  # Run with stdio for direct execution
