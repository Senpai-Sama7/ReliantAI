# Local Super Agent: Your Personal AI Assistant

## A Simple Guide for Non-Technical Users

Welcome to your Local Super Agent! This powerful AI lives right on your computer and can help you with many tasks, from finding information online to organizing your files. It's designed to be easy to use, just like chatting with a friend.

---

## 1. Getting Started: Setting Up Your Agent

Before you can chat with your agent, you need to set it up. Don't worry, it's simpler than it sounds!

### What You Need:

*   **Python:** Think of Python as the language your computer needs to understand the agent. If you don't have it, you can download it from [python.org](https://www.python.org/downloads/).
*   **A Folder:** Your agent lives in a special folder on your computer. This is the `Citadel` folder you've been working with.

### Step-by-Step Setup:

1.  **Open Your Terminal/Command Prompt:**
    *   **Windows:** Search for "Command Prompt" or "PowerShell" in your Start Menu.
    *   **macOS/Linux:** Search for "Terminal" in your Applications or Utilities folder.

2.  **Go to Your Agent's Folder:**
    In the Terminal/Command Prompt, type this command and press Enter:
    ```bash
cd /path/to/your/Citadel
    ```
    (This command tells your computer to go into the `Citadel` folder.)

3.  **Install Agent's Tools:**
    Now, type this command and press Enter:
    ```bash
    pip install -r local_agent/requirements.txt
    ```
    (This command installs all the necessary "tools" the agent needs to work. It might take a few minutes.)

4.  **Run Your Agent!**
    Finally, type this command and press Enter:
    ```bash
    python local_agent/gui.py
    ```
    (This command starts your agent's desktop application. A new window should pop up!)

    *   **Keep this Terminal/Command Prompt window open!** If you close it, your agent will stop running.

### (Optional) One-Click App:

If you want to make your agent a single-click application (like other programs on your computer), you can use a tool called `PyInstaller`.

1.  **Install PyInstaller:**
    In your Terminal/Command Prompt (in the `Citadel` folder), type:
    ```bash
    pip install pyinstaller
    ```

2.  **Create the One-Click App:**
    Then type:
    ```bash
    pyinstaller --onefile --windowed --name LocalSuperAgent local_agent/gui.py
    ```
    This will create a new folder called `dist` inside your `Citadel` folder. Inside `dist`, you'll find an executable file named `LocalSuperAgent` (or `LocalSuperAgent.exe` on Windows). You can double-click this file to start your agent without using the Terminal/Command Prompt.

---

## 2. Using Your Agent: The Desktop Interface

Once the agent's window appears, you'll see a beautiful, retro-futuristic chat interface.

*   **Chat History:** The main area of the window shows your conversation with the agent.
*   **Input Box:** At the bottom, there's a box where you can type your messages.
*   **Send Button:** Click "Send" or press Enter on your keyboard to send your message.

**How to Talk to Your Agent:**

Just type what you want the agent to do or ask it a question, in plain English. The agent is designed to understand natural language and will try to figure out the best way to help you.

---

## 3. What Your Agent Can Do: Powerful Features

Your Local Super Agent is incredibly powerful and can do many things. It uses a "Plan-and-Execute" approach, meaning it will often think about a task, make a plan, and then carry it out.

### A. Running Commands on Your Computer (Requires Permission!)

Your agent can run commands on your computer, just like you would in a Terminal or Command Prompt. This is incredibly powerful, but also requires your careful attention.

*   **How to Ask:**
    *   "List all the files in this folder."
    *   "What's my current directory?"
    *   "Can you tell me the version of Python installed?"
    *   "Open the 'Documents' folder." (Note: "Open" might depend on your operating system's default programs.)
    *   "Create a new folder called 'MyNewProject'."

*   **Important: The "Allow/Deny" Pop-up:**
    Because running commands can change your computer, your agent will **always ask for your permission** before it runs a command (unless you've enabled Autonomous Mode - see Section 4).
    *   When the agent wants to run a command, a special message will appear in the chat window, showing you exactly what command it plans to execute.
    *   You will see two buttons: **"Allow"** and **"Deny"**.
    *   **Always read the command carefully!** If you understand it and trust it, click "Allow." If you're unsure or don't want it to run, click "Deny."

### B. Reading and Writing Files (Requires Permission!)

Your agent can read the content of files and even create or change files on your computer. This is how it can modify its own code!

*   **How to Ask:**
    *   "Read the content of my `notes.txt` file."
    *   "What's inside the file named `report.docx`?" (Note: It can read text from many file types, but complex formats like images or videos might not be fully understood.)
    *   "Write a new file called `todo.txt` with the text 'Buy groceries, call mom'."
    *   "Add 'Remember to water plants' to my `todo.txt` file."
    *   "Change the log level in `local_agent/config.json` to 'DEBUG'." (This is how it can modify its own settings!)

*   **Important: The "Allow/Deny" Pop-up:**
    Just like running commands, reading or writing files also requires your permission. The "Allow/Deny" pop-up will appear, showing you the file operation it intends to perform.

### C. Searching the Internet

Your agent can search the web to find information, just like a search engine.

*   **How to Ask:**
    *   "What's the weather like in London today?"
    *   "Tell me about the history of artificial intelligence."
    *   "Find recent news about space exploration."

*   **No Permission Needed:** The agent does not need your permission for web searches, as it doesn't change anything on your computer.

### D. Reading Webpages

If you have a specific web address (URL) and want your agent to read its content, it can do that too.

*   **How to Ask:**
    *   "Summarize the article at `https://example.com/news-article`."
    *   "What are the main points on `https://www.wikipedia.org/wiki/AI`?"

*   **No Permission Needed:** Similar to web searches, fetching webpage content does not require your permission.

### E. Managing Python Packages (Requires Permission!)

Your agent can install new Python software (packages) that it might need to perform tasks.

*   **How to Ask:**
    *   "Install the 'requests' Python package."
    *   "Can you install 'numpy' for me?"

*   **Important: The "Allow/Deny" Pop-up:**
    Installing software requires your permission.

### F. Running Tests (Requires Permission!)

If you're a developer, your agent can help you run tests for your code.

*   **How to Ask:**
    *   "Run all the tests in the current directory."
    *   "Run tests in the 'my_module/tests' folder."

*   **Important: The "Allow/Deny" Pop-up:**
    Running tests requires your permission.

### G. Using Git Commands (Requires Permission!)

For those who use Git (a tool for managing code changes), your agent can help with basic Git operations.

*   **How to Ask:**
    *   "What is the current Git status?"
    *   "Add all changes to Git."
    *   "Commit changes with the message 'Implemented new feature'."

*   **Important: The "Allow/Deny" Pop-up:**
    Git commands require your permission.

### H. Remembering Things (Persistent Memory)

Your agent can remember facts and information you tell it, and recall them later, even if you close and reopen the application.

*   **How to Ask it to Remember:**
    *   "Remember that my favorite color is blue."
    *   "Save this fact: The project deadline is next Friday."

*   **How to Ask it to Recall:**
    *   "What is my favorite color?"
    *   "What did I tell you about the project deadline?"

*   **No Permission Needed:** Remembering and recalling facts does not require your permission.

### I. Restarting Itself (Requires Permission!)

If the agent modifies its own code or settings, it will need to restart to apply those changes. It will tell you when this is needed.

*   **How it Works:**
    *   After making a change that requires a restart, the agent will tell you: "RESTART_SIGNAL: Agent needs to be restarted to apply changes. Please restart the application."
    *   You will then need to **manually close the agent's window** and **restart it** using the `python local_agent/gui.py` command (or by double-clicking the one-click executable).

*   **Important: The "Allow/Deny" Pop-up:**
    The agent will ask for your permission before signaling a restart.

---

## 4. Safety First: Understanding Permissions and Autonomous Mode

Your safety is the top priority. The "Allow/Deny" pop-up is your main safeguard.

*   **Always Review:** Before clicking "Allow," take a moment to understand what the agent wants to do. If you're unsure, click "Deny" and ask the agent to explain its plan in more detail.
*   **"Autonomous Mode" (Extremely Dangerous!):**
    Your agent has a special setting called "Autonomous Mode." When this is turned **OFF** (which is the default and safest setting), the agent will **always ask for your permission** for commands and file operations.

    If "Autonomous Mode" is turned **ON**, the agent will perform commands and file operations **without asking you first**. This is incredibly risky because a mistake by the AI could lead to:
    *   **Deleting your important files.**
    *   **Changing your computer's settings.**
    *   **Running harmful programs.**

    **We strongly recommend keeping "Autonomous Mode" OFF.**

### How to Toggle "Autonomous Mode" (Advanced Users Only):

If you absolutely understand the risks and wish to change this setting:

1.  **Close Your Agent:** Close the agent's desktop window and the Terminal/Command Prompt window where it was running.
2.  **Open `config.json`:**
    *   Go to your `Citadel` folder.
    *   Then go into the `local_agent` folder.
    *   Find the file named `config.json` and open it with a simple text editor (like Notepad on Windows, TextEdit on macOS, or any code editor).
3.  **Change the Setting:**
    You will see a line like this:
    ```json
    "autonomous_mode": false
    ```
    To turn Autonomous Mode ON, change `false` to `true`:
    ```json
    "autonomous_mode": true
    ```
4.  **Save and Restart:** Save the `config.json` file and then restart your agent using the steps in Section 1.

---

## 5. Troubleshooting (Basic)

*   **Agent Window Doesn't Appear:**
    *   Make sure you ran `python local_agent/gui.py` in the correct folder.
    *   Check the Terminal/Command Prompt window for any error messages.
*   **Agent Not Responding:**
    *   Ensure the Terminal/Command Prompt window where you started the agent is still open. If it's closed, the agent stops.
    *   Try closing the agent window and restarting it.
*   **Errors in Chat:**
    *   If the agent gives you an error message in the chat, try rephrasing your request.
    *   For persistent errors, you might need to consult someone more technical.

---

Enjoy exploring the capabilities of your Local Super Agent! Remember to always prioritize safety and review its actions carefully.